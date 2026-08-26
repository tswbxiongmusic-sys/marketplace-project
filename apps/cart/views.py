from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from apps.orders.models import Coupon, ShippingMethod
from apps.products.models import Product, Wishlist
from .models import CartItem


@login_required
def add_to_cart(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    product = get_object_or_404(Product.objects.published(), pk=pk)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    requested_quantity = item.quantity if created else item.quantity + 1
    if requested_quantity > product.stock:
        if created:
            item.delete()
        messages.error(request, f"ສິນຄ້າ {product.name} ເຫຼືອພຽງ {product.stock} ຊິ້ນ.")
        return redirect("product_detail", pk=product.pk)
    if not created:
        item.quantity = requested_quantity
        item.save(update_fields=["quantity", "updated_at"])
    messages.success(request, f"ເພີ່ມ {product.name} ໃສ່ກະຕ່າແລ້ວ.")
    return redirect("cart")


@login_required
def cart_view(request):

    items = CartItem.objects.filter(
        user=request.user
    ).select_related("product").prefetch_related("product__images")

    total = sum(
        item.product.price * item.quantity
        for item in items
    )

    shipping_methods = ShippingMethod.objects.filter(is_active=True)

    cart_product_ids = [item.product_id for item in items]
    recommended_products = (
        Product.objects.published()
        .exclude(id__in=cart_product_ids)
        .select_related("category")
        .prefetch_related("images")
        .order_by("?")[:4]
    )

    wishlisted_ids = set(
        Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
    )

    applied_coupon = None
    discount_amount = 0
    coupon_code = request.session.get("applied_coupon_code")
    if coupon_code:
        applied_coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
        error = applied_coupon.error_for(total) if applied_coupon else "ບໍ່ພົບລະຫັດຄູປອງນີ້."
        if error:
            messages.warning(request, f"ຄູປອງ {coupon_code}: {error}")
            request.session.pop("applied_coupon_code", None)
            applied_coupon = None
        else:
            discount_amount = applied_coupon.compute_discount(total)

    default_shipping_fee = shipping_methods[0].fee if shipping_methods else 0

    return render(
        request,
        "cart/cart.html",
        {
            "items": items,
            "total": total,
            "shipping_methods": shipping_methods,
            "recommended_products": recommended_products,
            "wishlisted_ids": wishlisted_ids,
            "applied_coupon": applied_coupon,
            "discount_amount": discount_amount,
            "subtotal_after_discount": total - discount_amount,
            "grand_total": total - discount_amount + default_shipping_fee,
        }
    )


@login_required
def apply_coupon(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    code = request.POST.get("code", "").strip()
    if not code:
        messages.error(request, "ກະລຸນາໃສ່ລະຫັດຄູປອງ.")
        return redirect("cart")

    items = CartItem.objects.filter(user=request.user).select_related("product")
    subtotal = sum(item.product.price * item.quantity for item in items)

    coupon = Coupon.objects.filter(code__iexact=code).first()
    if coupon is None:
        messages.error(request, "ບໍ່ພົບລະຫັດຄູປອງນີ້.")
        return redirect("cart")

    error = coupon.error_for(subtotal)
    if error:
        messages.error(request, error)
        return redirect("cart")

    request.session["applied_coupon_code"] = coupon.code
    messages.success(request, f"ນຳໃຊ້ຄູປອງ {coupon.code} ສຳເລັດແລ້ວ.")
    return redirect("cart")


@login_required
def remove_coupon(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    request.session.pop("applied_coupon_code", None)
    messages.info(request, "ນຳຄູປອງອອກແລ້ວ.")
    return redirect("cart")

@login_required
def update_cart_item(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    item = get_object_or_404(CartItem, pk=pk, user=request.user)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    if quantity < 1:
        item.delete()
        messages.info(request, "ລຶບສິນຄ້າອອກຈາກກະຕ່າແລ້ວ.")
    elif quantity > item.product.stock:
        messages.error(request, f"ສິນຄ້າ {item.product.name} ເຫຼືອພຽງ {item.product.stock} ຊິ້ນ.")
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        messages.success(request, "ອັບເດດຈຳນວນສິນຄ້າໃນກະຕ່າແລ້ວ.")
    return redirect("cart")


@login_required
def remove_cart_item(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    item = get_object_or_404(CartItem, pk=pk, user=request.user)
    item.delete()
    messages.info(request, "ລຶບສິນຄ້າອອກຈາກກະຕ່າແລ້ວ.")
    return redirect("cart")
