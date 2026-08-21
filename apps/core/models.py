from django.db import models


class StoreSettings(models.Model):
    """Single editable record for the public storefront identity."""

    name = models.CharField(max_length=120, default="ຕະຫຼາດອອນລາຍ")
    tagline = models.CharField(max_length=200, blank=True, default="ຊື້ງ່າຍ ຂາຍສະດວກ ໃນບ່ອນດຽວ")
    logo = models.ImageField(upload_to="store/", blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    facebook_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    bank_name = models.CharField(max_length=120, blank=True)
    bank_account_name = models.CharField(max_length=160, blank=True)
    bank_account_number = models.CharField(max_length=80, blank=True)
    payment_qr = models.ImageField(upload_to="store/payment_qr/", blank=True, null=True)
    transfer_instructions = models.TextField(blank=True)
    is_store_open = models.BooleanField(default=True)

    class Meta:
        verbose_name = "ຂໍ້ມູນຮ້ານ"
        verbose_name_plural = "ຂໍ້ມູນຮ້ານ"

    def __str__(self):
        return self.name
