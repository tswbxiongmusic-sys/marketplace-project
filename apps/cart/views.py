from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from apps.products.models import Product
from .models import CartItem


@login_required
def add_to_cart(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    product = get_object_or_404(Product, pk=pk, is_active=True)
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
    ).select_related("product")

    total = sum(
        item.product.price * item.quantity
        for item in items
    )

    return render(
        request,
        "cart/cart.html",
        {
            "items": items,
            "total": total,
        }
    )

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
