from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from apps.core.admin_utils import LaoAdminMixin

from .models import Category, Product, ProductImage, Review, SubCategory, Wishlist


@admin.register(Category)
class CategoryAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name_display", "slug_display")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    field_labels = {"name": "ຊື່ໝວດໝູ່", "slug": "Slug ສຳລັບ URL"}

    @admin.display(description="ຊື່ໝວດໝູ່", ordering="name")
    def name_display(self, obj):
        return obj.name

    @admin.display(description="Slug ສຳລັບ URL", ordering="slug")
    def slug_display(self, obj):
        return obj.slug


@admin.register(SubCategory)
class SubCategoryAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name_display", "category_display", "slug_display")
    list_filter = ("category",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    field_labels = {
        "category": "ໝວດໝູ່ຫຼັກ",
        "name": "ຊື່ໝວດຍ່ອຍ",
        "slug": "Slug ສຳລັບ URL",
    }

    @admin.display(description="ຊື່ໝວດຍ່ອຍ", ordering="name")
    def name_display(self, obj):
        return obj.name

    @admin.display(description="ໝວດໝູ່ຫຼັກ", ordering="category__name")
    def category_display(self, obj):
        return obj.category

    @admin.display(description="Slug ສຳລັບ URL", ordering="slug")
    def slug_display(self, obj):
        return obj.slug


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ("image", "alt_text", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 80px; max-width: 120px;" />', obj.image.url)
        return "ບໍ່ມີຮູບ"
    image_preview.short_description = "ຕົວຢ່າງຮູບ"


@admin.register(Product)
class ProductAdmin(LaoAdminMixin, admin.ModelAdmin):
    inlines = (ProductImageInline,)
    list_display = (
        "id",
        "name_display",
        "category_display",
        "subcategory_display",
        "seller_display",
        "price_display",
        "stock_display",
        "approval_status_display",
        "active_display",
        "image_preview",
    )
    list_display_links = ("id", "name_display")
    list_select_related = ("category", "subcategory", "seller")
    list_filter = (
        "approval_status",
        "category",
        "subcategory",
        "is_active",
        "seller",
    )
    search_fields = (
        "name",
        "slug",
        "description",
        "seller__username",
    )
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("image_preview", "created_at", "updated_at", "reviewed_at", "reviewed_by")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    actions = ("approve_products", "reject_products", "mark_as_active", "mark_as_inactive")
    fieldsets = (
        ("ລາຍລະອຽດສິນຄ້າ", {
            "fields": (
                "name",
                "slug",
                "category",
                "subcategory",
                "seller",
                "description",
                "price",
                "stock",
                "is_active",
                "image",
                "image_preview",
                "video",
            )
        }),
        ("ການກວດສອບຂອງ Admin", {
            "fields": ("approval_status", "rejection_reason", "reviewed_at", "reviewed_by"),
        }),
        ("Flash Sale (ບໍ່ບັງຄັບ)", {
            "fields": ("sale_price", "sale_ends_at"),
            "description": "ໃສ່ທັງ 2 ຊ່ອງນີ້ ຖ້າຢາກໃຫ້ສິນຄ້ານີ້ຂຶ້ນໃນແຖບ Flash Sale ໜ້າຫຼັກ.",
        }),
        ("ເວລາບັນທຶກ", {
            "fields": ("created_at", "updated_at"),
        }),
    )
    field_labels = {
        "name": "ຊື່ສິນຄ້າ",
        "slug": "Slug ສຳລັບ URL",
        "category": "ໝວດໝູ່",
        "subcategory": "ໝວດຍ່ອຍ",
        "seller": "ຜູ້ຂາຍ",
        "description": "ລາຍລະອຽດ",
        "price": "ລາຄາ",
        "stock": "ຈຳນວນໃນສາງ",
        "is_active": "ສະແດງໃນຮ້ານ",
        "image": "ຮູບຫຼັກ",
        "video": "ວິດີໂອອະທິບາຍສິນຄ້າ",
        "sale_price": "ລາຄາຫຼຸດ (Flash Sale)",
        "sale_ends_at": "ວັນ-ເວລາສິ້ນສຸດ Sale",
        "approval_status": "ສະຖານະການກວດສອບ",
        "rejection_reason": "ເຫດຜົນທີ່ປະຕິເສດ",
        "reviewed_at": "ວັນທີກວດສອບ",
        "reviewed_by": "ກວດສອບໂດຍ",
    }
    choice_labels = {
        "approval_status": dict(Product.APPROVAL_STATUS_CHOICES),
    }

    @admin.display(description="ຊື່ສິນຄ້າ", ordering="name")
    def name_display(self, obj):
        return obj.name

    @admin.display(description="ໝວດໝູ່", ordering="category__name")
    def category_display(self, obj):
        return obj.category

    @admin.display(description="ໝວດຍ່ອຍ", ordering="subcategory__name")
    def subcategory_display(self, obj):
        return obj.subcategory or "—"

    @admin.display(description="ຜູ້ຂາຍ", ordering="seller__username")
    def seller_display(self, obj):
        return obj.seller

    @admin.display(description="ລາຄາ", ordering="price")
    def price_display(self, obj):
        return f"₭{obj.price}"

    @admin.display(description="ຈຳນວນໃນສາງ", ordering="stock")
    def stock_display(self, obj):
        return obj.stock

    @admin.display(boolean=True, description="ສະແດງໃນຮ້ານ", ordering="is_active")
    def active_display(self, obj):
        return obj.is_active

    @admin.display(description="ສະຖານະການກວດສອບ", ordering="approval_status")
    def approval_status_display(self, obj):
        return obj.get_approval_status_display()

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.image.url)
        return "ບໍ່ມີຮູບ"
    image_preview.short_description = "ຕົວຢ່າງຮູບ"

    def approve_products(self, request, queryset):
        count = 0
        for product in queryset.exclude(approval_status=Product.APPROVED).select_related("seller"):
            product.approval_status = Product.APPROVED
            product.reviewed_at = timezone.now()
            product.reviewed_by = request.user
            product.save(update_fields=["approval_status", "reviewed_at", "reviewed_by"])
            product.seller.notifications.create(
                message=f"ສິນຄ້າ '{product.name}' ຖືກອະນຸມັດແລ້ວ, ຂຶ້ນຂາຍໃນຮ້ານແລ້ວ.",
                link=f"/products/{product.pk}/",
            )
            count += 1
        self.message_user(request, f"ອະນຸມັດ {count} ສິນຄ້າແລ້ວ.")
    approve_products.short_description = "ອະນຸມັດສິນຄ້າທີ່ເລືອກ"

    def reject_products(self, request, queryset):
        count = 0
        for product in queryset.exclude(approval_status=Product.REJECTED).select_related("seller"):
            product.approval_status = Product.REJECTED
            product.reviewed_at = timezone.now()
            product.reviewed_by = request.user
            product.save(update_fields=["approval_status", "reviewed_at", "reviewed_by"])
            product.seller.notifications.create(
                message=f"ສິນຄ້າ '{product.name}' ບໍ່ໄດ້ຮັບອະນຸມັດ. ກະລຸນາແກ້ໄຂ ແລະ ຕິດຕໍ່ຮ້ານ ຖ້າມີຄຳຖາມ.",
                link=f"/products/seller/products/{product.pk}/edit/",
            )
            count += 1
        self.message_user(request, f"ປະຕິເສດ {count} ສິນຄ້າແລ້ວ.")
    reject_products.short_description = "ປະຕິເສດສິນຄ້າທີ່ເລືອກ"

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"ສະແດງ {updated} ສິນຄ້າໃນຮ້ານແລ້ວ.")
    mark_as_active.short_description = "ໃຫ້ສິນຄ້າທີ່ເລືອກສະແດງໃນຮ້ານ"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"ເຊື່ອງ {updated} ສິນຄ້າຈາກຮ້ານແລ້ວ.")
    mark_as_inactive.short_description = "ເຊື່ອງສິນຄ້າທີ່ເລືອກຈາກຮ້ານ"


@admin.register(ProductImage)
class ProductImageAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("product_display", "alt_text_display", "created_display")
    search_fields = ("product__name", "alt_text")
    readonly_fields = ("created_at",)
    field_labels = {
        "product": "ສິນຄ້າ",
        "image": "ຮູບສິນຄ້າ",
        "alt_text": "ຄຳອະທິບາຍຮູບ",
        "created_at": "ສ້າງເມື່ອ",
    }

    @admin.display(description="ສິນຄ້າ", ordering="product__name")
    def product_display(self, obj):
        return obj.product

    @admin.display(description="ຄຳອະທິບາຍຮູບ", ordering="alt_text")
    def alt_text_display(self, obj):
        return obj.alt_text or "—"

    @admin.display(description="ສ້າງເມື່ອ", ordering="created_at")
    def created_display(self, obj):
        return obj.created_at


@admin.register(Review)
class ReviewAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("product_display", "user_display", "rating_display", "comment_display", "updated_display")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__username", "comment")
    readonly_fields = ("created_at", "updated_at")
    field_labels = {
        "product": "ສິນຄ້າ",
        "user": "ຜູ້ໃຊ້",
        "rating": "ຄະແນນ",
        "comment": "ຄຳເຫັນ",
        "created_at": "ສ້າງເມື່ອ",
        "updated_at": "ແກ້ໄຂເມື່ອ",
    }

    @admin.display(description="ສິນຄ້າ", ordering="product__name")
    def product_display(self, obj):
        return obj.product

    @admin.display(description="ຜູ້ໃຊ້", ordering="user__username")
    def user_display(self, obj):
        return obj.user

    @admin.display(description="ຄະແນນ", ordering="rating")
    def rating_display(self, obj):
        return f"{obj.rating}/5"

    @admin.display(description="ຄຳເຫັນ")
    def comment_display(self, obj):
        return obj.comment or "—"

    @admin.display(description="ແກ້ໄຂເມື່ອ", ordering="updated_at")
    def updated_display(self, obj):
        return obj.updated_at


@admin.register(Wishlist)
class WishlistAdmin(LaoAdminMixin, admin.ModelAdmin):
    list_display = ("user_display", "product_display", "created_display")
    search_fields = ("user__username", "product__name")
    readonly_fields = ("created_at",)
    field_labels = {"user": "ຜູ້ໃຊ້", "product": "ສິນຄ້າ", "created_at": "ສ້າງເມື່ອ"}

    @admin.display(description="ຜູ້ໃຊ້", ordering="user__username")
    def user_display(self, obj):
        return obj.user

    @admin.display(description="ສິນຄ້າ", ordering="product__name")
    def product_display(self, obj):
        return obj.product

    @admin.display(description="ເພີ່ມເມື່ອ", ordering="created_at")
    def created_display(self, obj):
        return obj.created_at
