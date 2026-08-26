from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "ລູກຄ້າ"
        SELLER = "SELLER", "ຜູ້ຂາຍ"
        ADMIN = "ADMIN", "ຜູ້ດູແລລະບົບ"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True
    )
    address = models.TextField(blank=True)
    seller_requested_at = models.DateTimeField(blank=True, null=True)
    seller_approved_at = models.DateTimeField(blank=True, null=True)

    # A suspension keeps the seller's account, login, and data intact but
    # blocks selling (unlike is_active, which would also block login
    # entirely) — used when a seller violates policy but shouldn't lose
    # their history/order records.
    is_suspended = models.BooleanField(default=False)
    suspended_at = models.DateTimeField(blank=True, null=True)
    suspension_reason = models.TextField(blank=True)

    # Each seller is an independent business with its own bank account, so
    # buyers must pay each seller in a cart separately rather than through
    # one shared store-wide QR code.
    bank_name = models.CharField(max_length=120, blank=True)
    bank_account_name = models.CharField(max_length=160, blank=True)
    bank_account_number = models.CharField(max_length=80, blank=True)
    payment_qr = models.ImageField(upload_to="sellers/payment_qr/", blank=True, null=True)

    # Storefront branding, set once a seller application is approved so the
    # rest of the site can show a real shop name/logo instead of a bare
    # username (seller directory, product detail "sold by", dashboard).
    store_name = models.CharField(max_length=150, blank=True)
    store_logo = models.ImageField(upload_to="sellers/store_logo/", blank=True, null=True)
    store_description = models.TextField(blank=True)
    store_category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    facebook_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    @property
    def display_name(self):
        return self.store_name or self.username

    def __str__(self):
        return self.username


class SellerApplication(models.Model):
    """A request from a user to become a seller.

    Kept separate from ``User`` because most of its fields (business type,
    registration number, verification document, the agreement checkboxes)
    only matter during the one-time review, whereas the storefront fields on
    ``User`` are live data used across the site.
    """

    INDIVIDUAL = "individual"
    COMPANY = "company"
    BUSINESS_TYPE_CHOICES = [
        (INDIVIDUAL, "ບຸກຄົນ / ຮ້ານຄ້າສ່ວນຕົວ"),
        (COMPANY, "ນິຕິບຸກຄົນ / ບໍລິສັດ"),
    ]

    PENDING = "pending"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    STATUS_CHOICES = [
        (PENDING, "ລໍຖ້າກວດສອບ"),
        (REVIEWING, "ກຳລັງກວດສອບ"),
        (APPROVED, "ອະນຸມັດແລ້ວ"),
        (REJECTED, "ປະຕິເສດ"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_applications",
    )
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default=INDIVIDUAL)
    business_registration_number = models.CharField(max_length=100, blank=True)
    verification_document = models.FileField(upload_to="sellers/verification/", blank=True, null=True)

    agreed_seller_agreement = models.BooleanField(default=False)
    agreed_privacy_policy = models.BooleanField(default=False)
    agreed_seller_rules = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_seller_applications",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "ໃບສະໝັກຜູ້ຂາຍ"
        verbose_name_plural = "ໃບສະໝັກຜູ້ຂາຍ"

    def __str__(self):
        return f"{self.user.username} — {self.get_status_display()}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
