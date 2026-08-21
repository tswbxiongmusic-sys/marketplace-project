from django.contrib import admin

from .admin_utils import LaoAdminMixin
from .models import StoreSettings


@admin.register(StoreSettings)
class StoreSettingsAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("store_name", "phone_number", "email_address", "open_status")
    fieldsets = (
        ("ຂໍ້ມູນພື້ນຖານ", {"fields": ("name", "tagline", "logo", "is_store_open")} ),
        ("ຂໍ້ມູນຕິດຕໍ່", {"fields": ("phone", "email", "address", "facebook_url", "tiktok_url", "youtube_url")} ),
        ("ຂໍ້ມູນຮັບຊຳລະ", {
            "description": "ໃສ່ຂໍ້ມູນນີ້ເພື່ອສະແດງໃນໜ້າຊຳລະເງິນ. ອັບໂຫຼດ QR ຂອງຮ້ານຖ້າຕ້ອງການຮັບໂອນດ້ວຍ QR.",
            "fields": (
                "bank_name",
                "bank_account_name",
                "bank_account_number",
                "payment_qr",
                "transfer_instructions",
            ),
        }),
    )
    field_labels = {
        "name": "ຊື່ຮ້ານ",
        "tagline": "ຄຳຂວັນຮ້ານ",
        "logo": "ໂລໂກ້ຮ້ານ",
        "is_store_open": "ເປີດໃຫ້ບໍລິການ",
        "phone": "ເບີໂທ",
        "email": "ອີເມວ",
        "address": "ທີ່ຢູ່",
        "facebook_url": "ລິ້ງ Facebook",
        "tiktok_url": "ລິ້ງ TikTok",
        "youtube_url": "ລິ້ງ YouTube",
        "bank_name": "ຊື່ທະນາຄານ",
        "bank_account_name": "ຊື່ບັນຊີ",
        "bank_account_number": "ເລກບັນຊີ",
        "payment_qr": "ຮູບ QR ຮັບເງິນ",
        "transfer_instructions": "ຄຳແນະນຳການໂອນ",
    }

    def has_add_permission(self, request):
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="ຊື່ຮ້ານ", ordering="name")
    def store_name(self, obj):
        return obj.name

    @admin.display(description="ເບີໂທ", ordering="phone")
    def phone_number(self, obj):
        return obj.phone or "—"

    @admin.display(description="ອີເມວ", ordering="email")
    def email_address(self, obj):
        return obj.email or "—"

    @admin.display(boolean=True, description="ເປີດໃຫ້ບໍລິການ", ordering="is_store_open")
    def open_status(self, obj):
        return obj.is_store_open
