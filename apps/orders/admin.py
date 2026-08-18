from django.contrib import admin
from apps.core.admin_utils import LaoAdminMixin, LaoInlineMixin

from .models import Order, OrderItem, OrderShipment, ShippingMethod


class OrderItemInline(LaoInlineMixin, admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ("product_display", "product_name_display", "unit_price_display", "quantity_display", "total_price_display")
    readonly_fields = fields

    @admin.display(description="ສິນຄ້າ")
    def product_display(self, obj):
        return obj.product

    @admin.display(description="ຊື່ສິນຄ້າ")
    def product_name_display(self, obj):
        return obj.product_name

    @admin.display(description="ລາຄາຕໍ່ໜ່ວຍ")
    def unit_price_display(self, obj):
        return f"₭{obj.unit_price}"

    @admin.display(description="ຈຳນວນ")
    def quantity_display(self, obj):
        return obj.quantity

    @admin.display(description="ລວມ")
    def total_price_display(self, obj):
        return f"₭{obj.total_price}"


class OrderShipmentInline(LaoInlineMixin, admin.TabularInline):
    model = OrderShipment
    extra = 0
    autocomplete_fields = ("seller",)
    fields = (
        "seller",
        "status",
        "carrier",
        "tracking_number",
        "shipped_at",
        "delivered_at",
    )


@admin.register(ShippingMethod)
class ShippingMethodAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("name", "fee_display", "estimated_delivery", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "estimated_delivery")
    ordering = ("sort_order", "fee", "name")
    field_labels = {
        "name": "ຊື່ວິທີຈັດສົ່ງ",
        "fee": "ຄ່າຂົນສົ່ງ",
        "estimated_delivery": "ໄລຍະເວລາຄາດຄະເນ",
        "is_active": "ເປີດໃຊ້",
        "sort_order": "ລຳດັບສະແດງ",
    }

    @admin.display(description="ຄ່າຂົນສົ່ງ", ordering="fee")
    def fee_display(self, obj):
        return f"₭{obj.fee}"


@admin.register(Order)
class OrderAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = (
        "order_number_display",
        "user_display",
        "status_display",
        "payment_method_display",
        "payment_status_display",
        "shipping_method_display",
        "total_price_display",
        "created_at_display",
        "item_count",
    )
    list_select_related = ("user", "shipping_method")
    list_filter = (
        "status",
        "payment_method",
        "payment_status",
        "shipping_method",
        "created_at",
    )
    search_fields = (
        "order_number",
        "user__username",
        "recipient_name",
        "phone",
        "items__product_name",
    )
    readonly_fields = (
        "order_number_display",
        "created_at_display",
        "total_price_display",
    )
    inlines = (OrderItemInline, OrderShipmentInline)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    actions = (
        "cancel_orders",
        "mark_as_paid",
        "mark_payment_as_failed",
        "mark_as_shipping",
        "mark_as_completed",
    )
    fieldsets = (
        ("ຂໍ້ມູນຄຳສັ່ງຊື້", {
            "fields": (
                "order_number_display",
                "user",
                "status",
                "payment_method",
                "payment_status",
                "payment_receipt",
                "shipping_method",
                "shipping_fee",
                "total_price_display",
                "created_at_display",
            )
        }),
        ("ຂໍ້ມູນຈັດສົ່ງ", {
            "fields": (
                "recipient_name",
                "phone",
                "shipping_address",
            )
        }),
    )
    field_labels = {
        "user": "ລູກຄ້າ",
        "status": "ສະຖານະຄຳສັ່ງຊື້",
        "payment_method": "ວິທີຊຳລະ",
        "payment_status": "ສະຖານະການຊຳລະ",
        "payment_receipt": "ຫຼັກຖານການໂອນ",
        "shipping_method": "ວິທີຈັດສົ່ງ",
        "shipping_fee": "ຄ່າຂົນສົ່ງ",
        "recipient_name": "ຊື່ຜູ້ຮັບ",
        "phone": "ເບີໂທ",
        "shipping_address": "ທີ່ຢູ່ຈັດສົ່ງ",
    }

    @admin.display(description="ເລກຄຳສັ່ງຊື້", ordering="order_number")
    def order_number_display(self, obj):
        return obj.order_number

    @admin.display(description="ລູກຄ້າ", ordering="user__username")
    def user_display(self, obj):
        return obj.user

    @admin.display(description="ສະຖານະ", ordering="status")
    def status_display(self, obj):
        return obj.get_status_display()

    @admin.display(description="ວິທີຊຳລະ", ordering="payment_method")
    def payment_method_display(self, obj):
        return obj.get_payment_method_display()

    @admin.display(description="ສະຖານະການຊຳລະ", ordering="payment_status")
    def payment_status_display(self, obj):
        return obj.get_payment_status_display()

    @admin.display(description="ວິທີຈັດສົ່ງ", ordering="shipping_method__name")
    def shipping_method_display(self, obj):
        return obj.shipping_method or "-"

    @admin.display(description="ຍອດລວມ", ordering="total_price")
    def total_price_display(self, obj):
        return f"₭{obj.total_price}"

    @admin.display(description="ສ້າງເມື່ອ", ordering="created_at")
    def created_at_display(self, obj):
        return obj.created_at

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "ຈຳນວນລາຍການ"

    @admin.action(description="ຍົກເລີກຄຳສັ່ງຊື້ທີ່ເລືອກ ແລະ ຄືນສິນຄ້າເຂົ້າສາງ")
    def cancel_orders(self, request, queryset):
        count = sum(order.cancel() for order in queryset)
        self.message_user(request, f"ຍົກເລີກ {count} ຄຳສັ່ງຊື້ ແລະ ຄືນສິນຄ້າເຂົ້າສາງແລ້ວ.")

    @admin.action(description="ຕັ້ງຄຳສັ່ງຊື້ທີ່ເລືອກວ່າຊຳລະແລ້ວ")
    def mark_as_paid(self, request, queryset):
        from .views import notify_order

        updated = 0
        for order in queryset.exclude(status="cancelled"):
            changed_fields = []
            if order.payment_status != "paid":
                order.payment_status = "paid"
                changed_fields.append("payment_status")
            if order.status == "pending":
                order.status = "paid"
                changed_fields.append("status")
            if changed_fields:
                order.save(update_fields=changed_fields)
                notify_order(order, f"ການຊຳລະສຳລັບຄຳສັ່ງຊື້ {order.order_number} ຂອງທ່ານໄດ້ຮັບການຢືນຢັນແລ້ວ.")
                updated += 1
        self.message_user(request, f"ຢືນຢັນການຊຳລະ {updated} ຄຳສັ່ງຊື້ແລ້ວ.")

    @admin.action(description="ຕັ້ງການຊຳລະຂອງຄຳສັ່ງຊື້ທີ່ເລືອກວ່າບໍ່ຜ່ານ")
    def mark_payment_as_failed(self, request, queryset):
        from .views import notify_order

        updated = 0
        for order in queryset.exclude(status="cancelled").exclude(payment_status="failed"):
            order.payment_status = "failed"
            order.save(update_fields=["payment_status"])
            notify_order(order, f"ຫຼັກຖານການຊຳລະຂອງຄຳສັ່ງຊື້ {order.order_number} ຍັງບໍ່ຜ່ານການກວດ. ກະລຸນາຕິດຕໍ່ຮ້ານ.")
            updated += 1
        self.message_user(request, f"ຕັ້ງການຊຳລະບໍ່ຜ່ານ {updated} ຄຳສັ່ງຊື້ແລ້ວ.")

    @admin.action(description="ຕັ້ງຄຳສັ່ງຊື້ທີ່ເລືອກວ່າກຳລັງຈັດສົ່ງ")
    def mark_as_shipping(self, request, queryset):
        updated = queryset.update(status="shipping")
        self.message_user(request, f"ຕັ້ງ {updated} ຄຳສັ່ງຊື້ວ່າກຳລັງຈັດສົ່ງ.")

    @admin.action(description="ຕັ້ງຄຳສັ່ງຊື້ທີ່ເລືອກວ່າສຳເລັດ")
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status="completed")
        self.message_user(request, f"ຕັ້ງ {updated} ຄຳສັ່ງຊື້ວ່າສຳເລັດແລ້ວ.")


@admin.register(OrderShipment)
class OrderShipmentAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = (
        "order_number_display",
        "seller",
        "status_display",
        "carrier",
        "tracking_number",
        "updated_at",
    )
    list_select_related = ("order", "seller")
    list_filter = ("status", "carrier")
    search_fields = ("order__order_number", "seller__username", "carrier", "tracking_number")
    autocomplete_fields = ("order", "seller")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    field_labels = {
        "order": "ຄຳສັ່ງຊື້",
        "seller": "ຜູ້ຂາຍ",
        "status": "ສະຖານະພັດສະດຸ",
        "carrier": "ຜູ້ຂົນສົ່ງ",
        "tracking_number": "ເລກຕິດຕາມ",
        "shipped_at": "ສົ່ງອອກເມື່ອ",
        "delivered_at": "ຮອດປາຍທາງເມື່ອ",
    }

    @admin.display(description="ເລກຄຳສັ່ງຊື້", ordering="order__order_number")
    def order_number_display(self, obj):
        return obj.order.order_number

    @admin.display(description="ສະຖານະ", ordering="status")
    def status_display(self, obj):
        return obj.get_status_display()
