from django.urls import path

from . import views


urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("sellers/", views.seller_list, name="seller_list"),
    path("seller/", views.seller_dashboard, name="seller_dashboard"),
    path("seller/payment/", views.seller_payment_settings, name="seller_payment_settings"),
    path(
        "seller/products/add/",
        views.add_product,
        name="add_product",
    ),
    path(
        "seller/products/<int:pk>/edit/",
        views.edit_product,
        name="edit_product",
    ),
    path(
        "seller/products/<int:pk>/archive/",
        views.archive_product,
        name="archive_product",
    ),
    path(
        "seller/products/<int:pk>/restore/",
        views.restore_product,
        name="restore_product",
    ),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("<int:pk>/wishlist/", views.toggle_wishlist, name="toggle_wishlist"),
    path("<int:pk>/review/", views.review_product, name="review_product"),
]
