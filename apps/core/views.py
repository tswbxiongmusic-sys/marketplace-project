from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET

from apps.products.models import Product, Category
from apps.products.forms import ReviewForm
from apps.products.models import Wishlist


def home(request):

    search = request.GET.get("search")

    # -----------------------------------------
    # Categories
    # -----------------------------------------
    categories = Category.objects.prefetch_related("subcategories").all().order_by("name")


    # -----------------------------------------
    # Base products
    # -----------------------------------------
    products = (
        Product.objects
        .filter(is_active=True)
        .select_related("category", "subcategory")
    )


    # -----------------------------------------
    # Search
    # -----------------------------------------
    if search:
        products = products.filter(
            name__icontains=search
        )


    # -----------------------------------------
    # Featured Products
    # -----------------------------------------
    featured_products = products.order_by(
        "-created_at"
    )[:8]


    # -----------------------------------------
    # Latest Products
    # -----------------------------------------
    latest_products = products.order_by(
        "-created_at"
    )[:12]


    return render(
        request,
        "core/home.html",
        {
            "categories": categories,
            "featured_products": featured_products,
            "latest_products": latest_products,
            "search": search,
        },
    )


def product_detail(request, pk):

    product = get_object_or_404(
        Product.objects.select_related("category", "subcategory").prefetch_related("images", "reviews__user"),
        pk=pk,
        is_active=True,
    )

    return render(
        request,
        "core/detail.html",
        {
            "product": product,
            "reviews": product.reviews.select_related("user").order_by("-created_at"),
            "review_form": ReviewForm(),
            "is_wishlisted": request.user.is_authenticated and Wishlist.objects.filter(user=request.user, product=product).exists(),
        },
    )


def store_info(request):
    """Show the public contact details configured by the administrator."""
    return render(request, "core/store_info.html")


def store_policies(request):
    """Show the customer policies that apply to this storefront."""
    return render(request, "core/store_policies.html")


@require_GET
def health_check(request):
    """A minimal readiness endpoint for the deployment platform."""
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
