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

    # Each seller is an independent business with its own bank account, so
    # buyers must pay each seller in a cart separately rather than through
    # one shared store-wide QR code.
    bank_name = models.CharField(max_length=120, blank=True)
    bank_account_name = models.CharField(max_length=160, blank=True)
    bank_account_number = models.CharField(max_length=80, blank=True)
    payment_qr = models.ImageField(upload_to="sellers/payment_qr/", blank=True, null=True)

    def __str__(self):
        return self.username


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
