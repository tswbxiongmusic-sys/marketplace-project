from django.urls import path
from . import views

urlpatterns = [
    path(
        "add/<int:pk>/",
        views.add_to_cart,
        name="add_to_cart",
    ),
    path("item/<int:pk>/update/", views.update_cart_item, name="update_cart_item"),
    path("item/<int:pk>/remove/", views.remove_cart_item, name="remove_cart_item"),
    path("coupon/apply/", views.apply_coupon, name="apply_coupon"),
    path("coupon/remove/", views.remove_coupon, name="remove_coupon"),
      path(
        "",
        views.cart_view,
        name="cart",
    )
]
