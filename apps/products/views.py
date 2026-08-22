from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.accounts.forms import SellerPaymentForm

from .forms import ProductForm, ReviewForm
from .models import Category, Product, ProductImage, Review, Wishlist

User = get_user_model()


def product_list(request):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category", "subcategory").prefetch_related("images")
        .order_by("-created_at")
    )

    categories = Category.objects.prefetch_related("subcategories").all().order_by("name")

    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()
    selected_subcategory = request.GET.get("subcategory", "").strip()
    selected_seller = request.GET.get("seller", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "newest")

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
        )

    if selected_category:
        products = products.filter(
            category__slug=selected_category
        )

    if selected_subcategory:
        products = products.filter(
            subcategory__slug=selected_subcategory
        )

    seller_store = None
    if selected_seller:
        seller_store = get_object_or_404(User, pk=selected_seller, role=User.Role.SELLER)
        products = products.filter(seller_id=selected_seller)

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    products = products.order_by({"price_low": "price", "price_high": "-price", "oldest": "created_at"}.get(sort, "-created_at"))

    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    wishlisted_ids = set(
        Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
    ) if request.user.is_authenticated else set()

    return render(
        request,
        "products/list.html",
        {
            "products": page_obj,
            "categories": categories,
            "query": query,
            "selected_category": selected_category,
            "selected_subcategory": selected_subcategory,
            "selected_seller": selected_seller,
            "seller_store": seller_store,
            "page_obj": page_obj,
            "min_price": min_price, "max_price": max_price, "sort": sort,
            "wishlisted_ids": wishlisted_ids,
        },
    )


def seller_list(request):
    query = request.GET.get("q", "").strip()

    sellers = (
        User.objects.filter(role=User.Role.SELLER, is_active=True)
        .annotate(product_count=Count("products", filter=Q(products__is_active=True)))
        .order_by("-seller_approved_at", "username")
    )

    if query:
        sellers = sellers.filter(username__icontains=query)

    paginator = Paginator(sellers, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "products/seller_list.html",
        {
            "sellers": page_obj,
            "page_obj": page_obj,
            "query": query,
        },
    )


@login_required
def seller_dashboard(request):
    if request.user.role != request.user.Role.SELLER:
        messages.error(request, "ສ່ວນນີ້ສຳລັບຜູ້ຂາຍເທົ່ານັ້ນ.")
        return redirect("home")

    products = (
        Product.objects.filter(seller=request.user)
        .select_related("category")
        .order_by("-created_at")
    )

    return render(
        request,
        "products/seller_dashboard.html",
        {"products": products, "payment_form": SellerPaymentForm(instance=request.user)},
    )


@login_required
def seller_payment_settings(request):
    if request.user.role != request.user.Role.SELLER:
        messages.error(request, "ສ່ວນນີ້ສຳລັບຜູ້ຂາຍເທົ່ານັ້ນ.")
        return redirect("home")

    if request.method != "POST":
        return redirect("seller_dashboard")

    form = SellerPaymentForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "ບັນທຶກຂໍ້ມູນຮັບເງິນແລ້ວ.")
        return redirect("seller_dashboard")

    products = (
        Product.objects.filter(seller=request.user)
        .select_related("category")
        .order_by("-created_at")
    )
    return render(
        request,
        "products/seller_dashboard.html",
        {"products": products, "payment_form": form},
    )


@login_required
def add_product(request):
    if request.user.role != request.user.Role.SELLER:
        messages.error(request, "ສ່ວນນີ້ສຳລັບຜູ້ຂາຍເທົ່ານັ້ນ.")
        return redirect("home")

    form = ProductForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.save()
        for image in request.FILES.getlist("gallery_images"):
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, "ເພີ່ມສິນຄ້າສຳເລັດແລ້ວ.")
        return redirect("seller_dashboard")

    return render(
        request,
        "products/add_product.html",
        {"form": form},
    )


@login_required
def edit_product(request, pk):
    if request.user.role != request.user.Role.SELLER:
        messages.error(request, "ສ່ວນນີ້ສຳລັບຜູ້ຂາຍເທົ່ານັ້ນ.")
        return redirect("home")

    product = get_object_or_404(
        Product,
        pk=pk,
        seller=request.user,
    )

    form = ProductForm(
        request.POST or None,
        request.FILES or None,
        instance=product,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        for image in request.FILES.getlist("gallery_images"):
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, "ອັບເດດສິນຄ້າສຳເລັດແລ້ວ.")
        return redirect("seller_dashboard")

    return render(
        request,
        "products/edit_product.html",
        {
            "form": form,
            "product": product,
        },
    )


@login_required
@require_POST
def archive_product(request, pk):
    if request.user.role != request.user.Role.SELLER:
        messages.error(request, "ສ່ວນນີ້ສຳລັບຜູ້ຂາຍເທົ່ານັ້ນ.")
        return redirect("home")

    product = get_object_or_404(
        Product,
        pk=pk,
        seller=request.user,
    )

    if product.is_active:
        product.is_active = False
        product.save(update_fields=["is_active"])
        messages.success(request, "ເຊື່ອງສິນຄ້າຈາກຮ້ານແລ້ວ.")
    else:
        messages.info(request, "ສິນຄ້ານີ້ຖືກເຊື່ອງຢູ່ແລ້ວ.")

    return redirect("seller_dashboard")


@login_required
@require_POST
def restore_product(request, pk):
    if request.user.role != request.user.Role.SELLER:
        messages.error(request, "ສ່ວນນີ້ສຳລັບຜູ້ຂາຍເທົ່ານັ້ນ.")
        return redirect("home")

    product = get_object_or_404(
        Product,
        pk=pk,
        seller=request.user,
    )

    if not product.is_active:
        product.is_active = True
        product.save(update_fields=["is_active"])
        messages.success(request, "ສະແດງສິນຄ້າໃນຮ້ານອີກຄັ້ງແລ້ວ.")
    else:
        messages.info(request, "ສິນຄ້ານີ້ສະແດງຢູ່ແລ້ວ.")

    return redirect("seller_dashboard")


@login_required
@require_POST
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, "ເພີ່ມເຂົ້າລາຍການທີ່ມັກແລ້ວ.")
    else:
        item.delete()
        messages.info(request, "ນຳອອກຈາກລາຍການທີ່ມັກແລ້ວ.")

    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("product_detail", pk=pk)


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product", "product__category")
    return render(request, "products/wishlist.html", {"items": items})


@login_required
@require_POST
def review_product(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    if product.seller_id == request.user.id:
        messages.error(request, "ທ່ານບໍ່ສາມາດຣີວິວສິນຄ້າຂອງຕົນເອງໄດ້.")
        return redirect("product_detail", pk=pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        Review.objects.update_or_create(product=product, user=request.user, defaults=form.cleaned_data)
        messages.success(request, "ບັນທຶກຣີວິວແລ້ວ.")
    else:
        messages.error(request, "ກະລຸນາເລືອກຄະແນນລະຫວ່າງ 1 ຫາ 5.")
    return redirect("product_detail", pk=pk)
