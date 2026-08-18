from django.db import models
from django.conf import settings
from apps.products.models import Product


class CartItem(models.Model):

    user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE
)


    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )


    quantity = models.PositiveIntegerField(
        default=1
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    def total_price(self):
        return self.product.price * self.quantity


    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="unique_cart_item_per_user_product"
            )
        ]
