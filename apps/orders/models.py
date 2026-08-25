import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Sum
from django.conf import settings
from django.utils import timezone
from apps.products.models import Product


def generate_order_number():
    return f"ORD-{uuid.uuid4().hex[:10].upper()}"


class Coupon(models.Model):
    """A discount code the store owner can create and hand out to customers."""

    PERCENT = "percent"
    FIXED = "fixed"
    DISCOUNT_TYPE_CHOICES = [
        (PERCENT, "ເປີເຊັນ (%)"),
        (FIXED, "ຈຳນວນເງິນຄົງທີ່ (₭)"),
    ]

    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default=PERCENT)
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(
        null=True, blank=True, help_text="ປ່ອຍວ່າງໄວ້ = ບໍ່ຈຳກັດຈຳນວນຄັ້ງ"
    )
    times_used = models.PositiveIntegerField(default=0, editable=False)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ຄູປອງສ່ວນຫຼຸດ"
        verbose_name_plural = "ຄູປອງສ່ວນຫຼຸດ"

    def __str__(self):
        if self.discount_type == self.PERCENT:
            return f"{self.code} (-{self.discount_value}%)"
        return f"{self.code} (-₭{self.discount_value:,.0f})"

    def error_for(self, subtotal):
        """Return a Lao-language error string if this coupon cannot be used, else None."""
        now = timezone.now()
        if not self.is_active:
            return "ຄູປອງນີ້ຖືກປິດໃຊ້ງານແລ້ວ."
        if self.valid_from and now < self.valid_from:
            return "ຄູປອງນີ້ຍັງບໍ່ທັນເຖິງເວລາໃຊ້ງານ."
        if self.valid_until and now > self.valid_until:
            return "ຄູປອງນີ້ໝົດອາຍຸແລ້ວ."
        if self.max_uses is not None and self.times_used >= self.max_uses:
            return "ຄູປອງນີ້ຖືກໃຊ້ຄົບຈຳນວນແລ້ວ."
        if subtotal < self.min_order_amount:
            return f"ຄູປອງນີ້ໃຊ້ໄດ້ເມື່ອຊື້ຄົບ ₭{self.min_order_amount:,.0f}."
        return None

    def compute_discount(self, subtotal):
        subtotal = Decimal(subtotal)
        if self.discount_type == self.PERCENT:
            discount = (subtotal * self.discount_value / Decimal("100"))
        else:
            discount = self.discount_value
        return min(discount, subtotal).quantize(Decimal("1"))


class ShippingMethod(models.Model):
    """A delivery option configured by the store administrator."""

    name = models.CharField(max_length=100, unique=True)
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estimated_delivery = models.CharField(
        max_length=100,
        blank=True,
        help_text="ເຊັ່ນ: 2-5 ມື້",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "fee", "name")
        verbose_name = "ວິທີຈັດສົ່ງ"
        verbose_name_plural = "ວິທີຈັດສົ່ງ"

    def __str__(self):
        estimate = f" · {self.estimated_delivery}" if self.estimated_delivery else ""
        return f"{self.name} — ₭{self.fee:,.0f}{estimate}"


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "ລໍຖ້າດຳເນີນການ"),
        ("paid", "ຊຳລະແລ້ວ"),
        ("shipping", "ກຳລັງຈັດສົ່ງ"),
        ("completed", "ສຳເລັດ"),
        ("cancelled", "ຍົກເລີກ"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cash_on_delivery", "ຈ່າຍເງິນປາຍທາງ"),
        ("bank_transfer", "ໂອນຜ່ານທະນາຄານ"),
        ("qr_payment", "ຊຳລະດ້ວຍ QR"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "ລໍຖ້າການຊຳລະ"),
        ("paid", "ຊຳລະແລ້ວ"),
        ("failed", "ຊຳລະບໍ່ສຳເລັດ"),
    ]

    order_number = models.CharField(
        max_length=20, default=generate_order_number, unique=True, editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    recipient_name = models.CharField(max_length=150)

    phone = models.CharField(max_length=20)

    shipping_address = models.TextField()

    # It remains nullable only so historical orders created before delivery
    # methods existed can be preserved without changing their totals.
    shipping_method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
    )
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_method = models.CharField(
    max_length=30,
    choices=PAYMENT_METHOD_CHOICES,
    default="cash_on_delivery"
)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )
    payment_receipt = models.ImageField(upload_to="payment_receipts/", blank=True, null=True)

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.order_number

    @property
    def items_total(self):
        """The product-only subtotal, kept separate from the delivery fee."""
        prefetched_items = self._prefetched_objects_cache.get("items")
        if prefetched_items is not None:
            return sum((item.total_price for item in prefetched_items), Decimal("0"))
        return self.items.aggregate(total=Sum("total_price"))["total"] or Decimal("0")

    def get_status_badge_class(self):
        return {
            "pending": "bg-warning text-dark",
            "paid": "bg-primary",
            "shipping": "bg-info text-dark",
            "completed": "bg-success",
            "cancelled": "bg-danger",
        }.get(self.status, "bg-secondary")

    @property
    def status_step(self):
        """Which stage (1-3) of the fulfillment tracker this order has reached."""
        return {
            "pending": 1,
            "paid": 1,
            "shipping": 2,
            "completed": 3,
        }.get(self.status, 1)

    def cancel(self):
        """Cancel once and return reserved stock to inventory."""
        if self.status not in {"pending", "paid"}:
            return False
        with transaction.atomic():
            locked_order = Order.objects.select_for_update().get(pk=self.pk)
            if locked_order.status == "cancelled":
                return False
            for item in locked_order.items.select_related("product"):
                Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
            locked_order.shipments.exclude(status="delivered").update(status="cancelled")
            locked_order.status = "cancelled"
            locked_order.save(update_fields=["status"])
        self.status = "cancelled"
        return True


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.order.order_number} — {self.product_name}"


class OrderShipment(models.Model):
    """One seller's parcel within an order.

    A cart can contain products from multiple sellers.  Each seller therefore
    receives an independent shipment record and cannot edit another seller's
    delivery status or tracking number.
    """

    STATUS_CHOICES = [
        ("pending", "ກຳລັງກະກຽມສິນຄ້າ"),
        ("shipping", "ກຳລັງຈັດສົ່ງ"),
        ("delivered", "ຈັດສົ່ງແລ້ວ"),
        ("cancelled", "ຍົກເລີກ"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="shipments")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="shipments",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    carrier = models.CharField(max_length=120, blank=True)
    tracking_number = models.CharField(max_length=120, blank=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("order", "seller"),
                name="unique_order_shipment_per_seller",
            )
        ]
        ordering = ("-created_at", "pk")
        verbose_name = "ພັດສະດຸ"
        verbose_name_plural = "ພັດສະດຸ"

    def __str__(self):
        return f"{self.order.order_number} — {self.seller}"

    def get_status_badge_class(self):
        return {
            "pending": "bg-warning text-dark",
            "shipping": "bg-info text-dark",
            "delivered": "bg-success",
            "cancelled": "bg-danger",
        }.get(self.status, "bg-secondary")
