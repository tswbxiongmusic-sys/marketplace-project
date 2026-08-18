import uuid
from decimal import Decimal

from django.db import models, transaction
from django.db.models import F, Sum
from django.conf import settings
from apps.products.models import Product


def generate_order_number():
    return f"ORD-{uuid.uuid4().hex[:10].upper()}"


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
