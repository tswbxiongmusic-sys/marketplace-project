from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from apps.core.admin_utils import LaoAdminMixin

from .models import Notification, SellerApplication, User


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
            "ຂໍ້ມູນຮ້ານ (ສຳລັບຜູ້ຂາຍ)",
            {
                "fields": (
                    "store_name", "store_logo", "store_category", "store_description",
                    "facebook_url", "tiktok_url", "website_url",
                )
            },
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
        "store_name": "ຊື່ຮ້ານ",
        "store_logo": "ໂລໂກ້ຮ້ານ",
        "store_category": "ປະເພດສິນຄ້າ",
        "store_description": "ຄຳອະທິບາຍຮ້ານ",
        "facebook_url": "Facebook Page",
        "tiktok_url": "TikTok",
        "website_url": "Website ຂອງຮ້ານ",
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
        queryset.filter(seller_requested_at__isnull=False).update(role=User.Role.SELLER, seller_approved_at=timezone.now())


@admin.register(SellerApplication)
class SellerApplicationAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("user_display", "store_name_display", "business_type_display", "status_display", "created_display")
    list_filter = ("status", "business_type")
    search_fields = ("user__username", "user__email", "user__store_name")
    ordering = ("-created_at",)
    readonly_fields = ("user", "created_at", "reviewed_at", "reviewed_by")
    actions = ("approve_applications", "reject_applications")

    fieldsets = (
        (
            "ຜູ້ສະໝັກ",
            {"fields": ("user",)},
        ),
        (
            "ຂໍ້ມູນທຸລະກິດ",
            {"fields": ("business_type", "business_registration_number", "verification_document")},
        ),
        (
            "ການຍອມຮັບ",
            {"fields": ("agreed_seller_agreement", "agreed_privacy_policy", "agreed_seller_rules")},
        ),
        (
            "ສະຖານະການກວດສອບ",
            {"fields": ("status", "rejection_reason", "reviewed_at", "reviewed_by", "created_at")},
        ),
    )

    field_labels = {
        "user": "ຜູ້ສະໝັກ",
        "business_type": "ປະເພດທຸລະກິດ",
        "business_registration_number": "ເລກຈົດທະບຽນທຸລະກິດ",
        "verification_document": "ຮູບ/ເອກະສານຢືນຢັນ",
        "agreed_seller_agreement": "ຍອມຮັບ Seller Agreement",
        "agreed_privacy_policy": "ຍອມຮັບ Privacy Policy",
        "agreed_seller_rules": "ຮັບຮູ້ Seller Rules",
        "status": "ສະຖານະ",
        "rejection_reason": "ເຫດຜົນທີ່ປະຕິເສດ",
        "reviewed_at": "ວັນທີກວດສອບ",
        "reviewed_by": "ກວດສອບໂດຍ",
        "created_at": "ວັນທີສະໝັກ",
    }
    choice_labels = {
        "business_type": dict(SellerApplication.BUSINESS_TYPE_CHOICES),
        "status": dict(SellerApplication.STATUS_CHOICES),
    }

    @admin.display(description="ຜູ້ສະໝັກ", ordering="user__username")
    def user_display(self, obj):
        return obj.user.username

    @admin.display(description="ຊື່ຮ້ານ", ordering="user__store_name")
    def store_name_display(self, obj):
        return obj.user.store_name or "—"

    @admin.display(description="ປະເພດທຸລະກິດ", ordering="business_type")
    def business_type_display(self, obj):
        return obj.get_business_type_display()

    @admin.display(description="ສະຖານະ", ordering="status")
    def status_display(self, obj):
        return obj.get_status_display()

    @admin.display(description="ວັນທີສະໝັກ", ordering="created_at")
    def created_display(self, obj):
        return obj.created_at

    @admin.action(description="ອະນຸມັດໃບສະໝັກທີ່ເລືອກ")
    def approve_applications(self, request, queryset):
        count = 0
        for application in queryset.exclude(status=SellerApplication.APPROVED).select_related("user"):
            application.status = SellerApplication.APPROVED
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.save(update_fields=["status", "reviewed_at", "reviewed_by"])

            user = application.user
            user.role = User.Role.SELLER
            user.seller_approved_at = timezone.now()
            user.save(update_fields=["role", "seller_approved_at"])

            user.notifications.create(
                message="ຍິນດີດ້ວຍ! ຮ້ານຂອງທ່ານໄດ້ຮັບອະນຸມັດແລ້ວ, ເລີ່ມເພີ່ມສິນຄ້າໄດ້ເລີຍ.",
                link="/products/seller/",
            )
            count += 1
        self.message_user(request, f"ອະນຸມັດ {count} ໃບສະໝັກແລ້ວ.")

    @admin.action(description="ປະຕິເສດໃບສະໝັກທີ່ເລືອກ")
    def reject_applications(self, request, queryset):
        count = 0
        for application in queryset.exclude(status=SellerApplication.REJECTED).select_related("user"):
            application.status = SellerApplication.REJECTED
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.save(update_fields=["status", "reviewed_at", "reviewed_by"])

            application.user.notifications.create(
                message="ຂໍອະໄພ, ໃບສະໝັກເປັນຜູ້ຂາຍຂອງທ່ານຍັງບໍ່ໄດ້ຮັບອະນຸມັດ. ກະລຸນາຕິດຕໍ່ຮ້ານ ຫຼື ສະໝັກໃໝ່ອີກຄັ້ງ.",
                link="/accounts/seller-application/",
            )
            count += 1
        self.message_user(request, f"ປະຕິເສດ {count} ໃບສະໝັກແລ້ວ.")


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
