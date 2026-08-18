from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.store_info, name="store_info"),
    path("policies/", views.store_policies, name="store_policies"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("health/", views.health_check, name="health_check"),
]
