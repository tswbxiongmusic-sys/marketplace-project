from django.contrib import admin
from apps.core.admin_utils import LaoAdminMixin

from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("user_display", "product_display", "quantity_display", "updated_display")
    search_fields = ("user__username", "product__name")
    readonly_fields = ("created_at", "updated_at")
    field_labels = {
        "user": "ຜູ້ໃຊ້",
        "product": "ສິນຄ້າ",
        "quantity": "ຈຳນວນ",
        "created_at": "ສ້າງເມື່ອ",
        "updated_at": "ອັບເດດເມື່ອ",
    }

    @admin.display(description="ຜູ້ໃຊ້", ordering="user__username")
    def user_display(self, obj):
        return obj.user

    @admin.display(description="ສິນຄ້າ", ordering="product__name")
    def product_display(self, obj):
        return obj.product

    @admin.display(description="ຈຳນວນ", ordering="quantity")
    def quantity_display(self, obj):
        return obj.quantity

    @admin.display(description="ອັບເດດເມື່ອ", ordering="updated_at")
    def updated_display(self, obj):
        return obj.updated_at
