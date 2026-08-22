from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Prefetch
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.mail import send_mail

from apps.cart.models import CartItem
from apps.products.models import Product

from .forms import CheckoutForm
from .models import Coupon, Order, OrderItem, OrderShipment, ShippingMethod


def notify_order(order, message):
    from apps.accounts.models import Notification
    Notification.objects.create(user=order.user, message=message, link=f"/orders/my-orders/{order.pk}/")
    if order.user.email:
        send_mail("ແຈ້ງເຕືອນຄຳສັ່ງຊື້", message, None, [order.user.email], fail_silently=True)


def checkout_context(request, form):
    """Render checkout consistently after both GET and form validation errors."""
    items = CartItem.objects.filter(user=request.user).select_related("product")
    total = sum((item.product.price * item.quantity for item in items), start=0)
    shipping_methods = list(ShippingMethod.objects.filter(is_active=True))

    applied_coupon = None
    discount_amount = 0
    coupon_code = request.session.get("applied_coupon_code")
    if coupon_code:
        coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
        if coupon and not coupon.error_for(total):
            applied_coupon = coupon
            discount_amount = coupon.compute_discount(total)

    return {
        "items": items,
        "total": total,
        "form": form,
        "shipping_methods": shipping_methods,
        "shipping_method_fees": {
            str(method.pk): str(method.fee) for method in shipping_methods
        },
        "applied_coupon": applied_coupon,
        "discount_amount": discount_amount,
        "subtotal_after_discount": total - discount_amount,
    }


def update_order_fulfillment_status(order):
    """Keep the buyer-facing order status in sync with seller parcels."""
    if order.status == "cancelled":
        return

    shipment_statuses = list(order.shipments.values_list("status", flat=True))
    if not shipment_statuses:
        return

    if all(status == "delivered" for status in shipment_statuses):
        next_status = "completed"
    elif any(status in {"shipping", "delivered"} for status in shipment_statuses):
        next_status = "shipping"
    else:
        # Do not overwrite the payment confirmation on a parcel that has not
        # left the seller yet.
        next_status = "paid" if order.payment_status == "paid" else "pending"

    if order.status != next_status:
        order.status = next_status
        order.save(update_fields=["status"])


@login_required
def checkout(request):
    form = CheckoutForm(
        initial={
            "recipient_name": request.user.get_full_name(),
            "phone": request.user.phone,
            "shipping_address": request.user.address,
        }
    )
    return render(request, "orders/checkout.html", checkout_context(request, form))


@login_required
def place_order(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    form = CheckoutForm(request.POST, request.FILES)

    if not form.is_valid():
        return render(request, "orders/checkout.html", checkout_context(request, form))

    with transaction.atomic():
        items = list(
            CartItem.objects.select_for_update()
            .filter(user=request.user)
            .select_related("product")
        )

        if not items:
            messages.info(request, "ກະຕ່າຂອງທ່ານວ່າງ.")
            return redirect("cart")

        product_ids = [item.product_id for item in items]

        products = {
            product.id: product
            for product in Product.objects.select_for_update().filter(
                id__in=product_ids,
                is_active=True,
            )
        }

        unavailable = [
            item.product.name
            for item in items
            if (
                item.product_id not in products
                or products[item.product_id].stock < item.quantity
            )
        ]

        if unavailable:
            messages.error(
                request,
                "ສິນຄ້າໃນສາງບໍ່ພໍສຳລັບ: " + ", ".join(unavailable) + ".",
            )
            return redirect("cart")

        product_total = sum(
            (item.product.price * item.quantity for item in items), start=0
        )
        shipping_method = form.cleaned_data["shipping_method"]

        coupon = None
        discount_amount = 0
        coupon_code = request.session.get("applied_coupon_code")
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
            if coupon is None or coupon.error_for(product_total):
                messages.warning(request, "ຄູປອງທີ່ນຳໃຊ້ບໍ່ສາມາດໃຊ້ໄດ້ອີກຕໍ່ໄປ, ຄຳສັ່ງຊື້ຈະດຳເນີນຕໍ່ໂດຍບໍ່ມີສ່ວນຫຼຸດ.")
                coupon = None
            else:
                discount_amount = coupon.compute_discount(product_total)

        order = Order.objects.create(
            user=request.user,
            recipient_name=form.cleaned_data["recipient_name"],
            phone=form.cleaned_data["phone"],
            shipping_address=form.cleaned_data["shipping_address"],
            shipping_method=shipping_method,
            payment_method=form.cleaned_data["payment_method"],
            payment_receipt=form.cleaned_data.get("payment_receipt"),
            shipping_fee=shipping_method.fee,
            coupon=coupon,
            discount_amount=discount_amount,
            total_price=product_total + shipping_method.fee - discount_amount,
        )

        if coupon is not None:
            Coupon.objects.filter(pk=coupon.pk).update(times_used=F("times_used") + 1)
            request.session.pop("applied_coupon_code", None)

        for item in items:
            product = products[item.product_id]

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=item.quantity,
                total_price=product.price * item.quantity,
            )

            Product.objects.filter(pk=product.pk).update(
                stock=F("stock") - item.quantity,
                updated_at=timezone.now(),
            )

        # Each seller owns only their parcel, even when one cart contains
        # products from multiple sellers.
        seller_ids = {products[item.product_id].seller_id for item in items}
        OrderShipment.objects.bulk_create(
            [OrderShipment(order=order, seller_id=seller_id) for seller_id in seller_ids]
        )

        CartItem.objects.filter(
            pk__in=[item.pk for item in items]
        ).delete()

        messages.success(request, "ສັ່ງຊື້ສຳເລັດແລ້ວ.")
        notify_order(order, f"ຄຳສັ່ງຊື້ {order.order_number} ຂອງທ່ານຖືກສ້າງແລ້ວ.")

    return redirect("order_detail", order_id=order.id)


@login_required
def my_orders(request):
    orders = (
        Order.objects.filter(user=request.user)
        .select_related("shipping_method")
        .prefetch_related("items", "shipments__seller")
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/my_orders.html",
        {"orders": orders},
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("shipping_method").prefetch_related("items", "shipments__seller"),
        pk=order_id,
        user=request.user,
    )

    return render(
        request,
        "orders/order_detail.html",
        {"order": order},
    )


@login_required
def seller_orders(request):
    if request.user.role != request.user.Role.SELLER:
        messages.error(request, "ສ່ວນນີ້ສຳລັບຜູ້ຂາຍເທົ່ານັ້ນ.")
        return redirect("home")

    shipments = (
        OrderShipment.objects.filter(seller=request.user)
        .select_related("order", "order__shipping_method")
        .prefetch_related(
            Prefetch(
                "order__items",
                queryset=OrderItem.objects.filter(product__seller=request.user).select_related("product"),
                to_attr="seller_items",
            )
        )
        .order_by("-order__created_at", "-pk")
    )

    return render(
        request,
        "orders/seller_orders.html",
        {"shipments": shipments},
    )


@login_required
def cancel_order(request, order_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if order.cancel():
        notify_order(order, f"ຄຳສັ່ງຊື້ {order.order_number} ຂອງທ່ານຖືກຍົກເລີກແລ້ວ.")
        messages.success(request, "ຍົກເລີກຄຳສັ່ງຊື້ແລ້ວ.")
    else:
        messages.error(request, "ຄຳສັ່ງຊື້ນີ້ບໍ່ສາມາດຍົກເລີກໄດ້ແລ້ວ.")
    return redirect("order_detail", order_id=order.pk)


@login_required
def update_shipment_status(request, shipment_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if request.user.role != request.user.Role.SELLER:
        messages.error(request, "ສ່ວນນີ້ສຳລັບຜູ້ຂາຍເທົ່ານັ້ນ.")
        return redirect("home")

    shipment = get_object_or_404(
        OrderShipment.objects.select_related("order"),
        pk=shipment_id,
        seller=request.user,
    )
    if shipment.order.status == "cancelled" or shipment.status in {"cancelled", "delivered"}:
        messages.error(request, "ພັດສະດຸນີ້ບໍ່ສາມາດອັບເດດໄດ້ແລ້ວ.")
        return redirect("seller_orders")

    # QR and bank-transfer orders must be confirmed by the shop before a
    # seller can dispatch them.  Cash-on-delivery orders remain dispatchable
    # while payment is pending because payment is collected on delivery.
    if (
        shipment.order.payment_method in {"bank_transfer", "qr_payment"}
        and shipment.order.payment_status != "paid"
    ):
        messages.error(
            request,
            "ກະລຸນາລໍຖ້າໃຫ້ຮ້ານຢືນຢັນການຊຳລະກ່ອນຈັດສົ່ງ.",
        )
        return redirect("seller_orders")

    status = request.POST.get("status")
    if status not in {"shipping", "delivered"}:
        messages.error(request, "ບໍ່ອະນຸຍາດໃຫ້ປ່ຽນສະຖານະນີ້.")
        return redirect("seller_orders")

    shipment.carrier = request.POST.get("carrier", "").strip()
    shipment.tracking_number = request.POST.get("tracking_number", "").strip()
    shipment.status = status
    update_fields = ["carrier", "tracking_number", "status", "updated_at"]
    if status == "shipping" and not shipment.shipped_at:
        shipment.shipped_at = timezone.now()
        update_fields.append("shipped_at")
    if status == "delivered":
        shipment.delivered_at = timezone.now()
        update_fields.append("delivered_at")
    shipment.save(update_fields=update_fields)

    update_order_fulfillment_status(shipment.order)
    tracking_detail = (
        f" ເລກຕິດຕາມ: {shipment.tracking_number}."
        if shipment.tracking_number
        else ""
    )
    notify_order(
        shipment.order,
        f"ພັດສະດຸສຳລັບຄຳສັ່ງຊື້ {shipment.order.order_number} "
        f"ປ່ຽນເປັນ {shipment.get_status_display()} ແລ້ວ.{tracking_detail}",
    )
    messages.success(request, "ອັບເດດພັດສະດຸ ແລະ ແຈ້ງລູກຄ້າແລ້ວ.")
    return redirect("seller_orders")
