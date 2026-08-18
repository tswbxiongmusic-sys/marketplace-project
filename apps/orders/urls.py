from django.urls import path

from . import views


urlpatterns = [
    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),
    path(
        "place-order/",
        views.place_order,
        name="place_order",
    ),
    path(
        "my-orders/",
        views.my_orders,
        name="my_orders",
    ),
    path(
        "my-orders/<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),
    path(
        "seller-orders/",
        views.seller_orders,
        name="seller_orders",
    ),
    path("my-orders/<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),
    path(
        "seller-shipments/<int:shipment_id>/status/",
        views.update_shipment_status,
        name="update_shipment_status",
    ),
]
