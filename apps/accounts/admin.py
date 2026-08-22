from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.core.admin_utils import LaoAdminMixin

from .models import Notification, User


@admin.register(User)
class CustomUserAdmin(LaoAdminMixin, UserAdmin):

    model = User

    list_display = (
        "username_display",
        "email_display",
        "role_display",
        "phone_display",
        "staff_display",
        "active_display",
    )

    list_display_links = (
        "username_display",
        "email_display",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "phone",
        "first_name",
        "last_name",
    )

    ordering = (
        "-date_joined",
    )

    fieldsets = (
        (
            "ຂໍ້ມູນການເຂົ້າໃຊ້",
            {"fields": ("username", "password")},
        ),
        (
            "ຂໍ້ມູນສ່ວນຕົວ",
            {"fields": ("first_name", "last_name", "email", "phone", "avatar", "address")},
        ),
        (
            "ບົດບາດຜູ້ໃຊ້",
            {"fields": ("role", "seller_requested_at", "seller_approved_at")},
        ),
        (
            "ຂໍ້ມູນຮັບເງິນ (ສຳລັບຜູ້ຂາຍ)",
            {"fields": ("bank_name", "bank_account_name", "bank_account_number", "payment_qr")},
        ),
        (
            "ສິດທິໃນລະບົບ",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "ວັນທີສຳຄັນ",
            {"fields": ("last_login", "date_joined")},
        ),
    )

    add_fieldsets = (
        (
            "ສ້າງບັນຊີໃໝ່",
            {
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "phone",
                    "avatar",
                    "address",
                )
            },
        ),
    )

    actions = ("approve_sellers",)
    field_labels = {
        "username": "ຊື່ຜູ້ໃຊ້",
        "password": "ລະຫັດຜ່ານ",
        "password1": "ລະຫັດຜ່ານ",
        "password2": "ຢືນຢັນລະຫັດຜ່ານ",
        "first_name": "ຊື່",
        "last_name": "ນາມສະກຸນ",
        "email": "ອີເມວ",
        "role": "ບົດບາດ",
        "phone": "ເບີໂທ",
        "avatar": "ຮູບໂປຣໄຟລ໌",
        "address": "ທີ່ຢູ່",
        "seller_requested_at": "ວັນທີສະໝັກເປັນຜູ້ຂາຍ",
        "seller_approved_at": "ວັນທີອະນຸມັດຜູ້ຂາຍ",
        "bank_name": "ຊື່ທະນາຄານ",
        "bank_account_name": "ຊື່ບັນຊີ",
        "bank_account_number": "ເລກບັນຊີ",
        "payment_qr": "ຮູບ QR ຮັບເງິນ",
        "is_active": "ເປີດໃຊ້ບັນຊີ",
        "is_staff": "ເຂົ້າໃຊ້ສ່ວນຈັດການໄດ້",
        "is_superuser": "ສິດສູງສຸດ",
        "groups": "ກຸ່ມ",
        "user_permissions": "ສິດທິຜູ້ໃຊ້",
        "last_login": "ເຂົ້າໃຊ້ຫຼ້າສຸດ",
        "date_joined": "ວັນທີສະໝັກ",
    }
    choice_labels = {
        "role": {
            User.Role.CUSTOMER: "ລູກຄ້າ",
            User.Role.SELLER: "ຜູ້ຂາຍ",
            User.Role.ADMIN: "ຜູ້ດູແລລະບົບ",
        },
    }

    @admin.display(description="ຊື່ຜູ້ໃຊ້", ordering="username")
    def username_display(self, obj):
        return obj.username

    @admin.display(description="ອີເມວ", ordering="email")
    def email_display(self, obj):
        return obj.email

    @admin.display(description="ບົດບາດ", ordering="role")
    def role_display(self, obj):
        return self.choice_labels["role"].get(obj.role, obj.role)

    @admin.display(description="ເບີໂທ", ordering="phone")
    def phone_display(self, obj):
        return obj.phone or "—"

    @admin.display(boolean=True, description="ເຂົ້າສ່ວນຈັດການໄດ້", ordering="is_staff")
    def staff_display(self, obj):
        return obj.is_staff

    @admin.display(boolean=True, description="ເປີດໃຊ້ບັນຊີ", ordering="is_active")
    def active_display(self, obj):
        return obj.is_active

    @admin.action(description="ອະນຸມັດຄຳຮ້ອງເປັນຜູ້ຂາຍທີ່ເລືອກ")
    def approve_sellers(self, request, queryset):
        from django.utils import timezone
        queryset.filter(seller_requested_at__isnull=False).update(role=User.Role.SELLER, seller_approved_at=timezone.now())


@admin.register(Notification)
class NotificationAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("user_display", "message_display", "read_display", "created_display")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "message")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    field_labels = {
        "user": "ຜູ້ໃຊ້",
        "message": "ຂໍ້ຄວາມ",
        "link": "ລິ້ງ",
        "is_read": "ອ່ານແລ້ວ",
        "created_at": "ສ້າງເມື່ອ",
    }

    @admin.display(description="ຜູ້ໃຊ້", ordering="user__username")
    def user_display(self, obj):
        return obj.user

    @admin.display(description="ຂໍ້ຄວາມ", ordering="message")
    def message_display(self, obj):
        return obj.message

    @admin.display(boolean=True, description="ອ່ານແລ້ວ", ordering="is_read")
    def read_display(self, obj):
        return obj.is_read

    @admin.display(description="ສ້າງເມື່ອ", ordering="created_at")
    def created_display(self, obj):
        return obj.created_at
