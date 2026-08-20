from django.db import models
from django.db.models import Avg
from django.conf import settings
from django.utils.text import slugify


def icon_for_name(name, fallback="🛍️"):
    label = (name or "").lower()
    icons = {
        "electronics": "💻", "electronic": "💻", "ເອເລັກໂຕຣນິກ": "💻",
        "iphone": "📱", "samsung": "📱", "phone": "📱", "mobile": "📱", "ໂທລະສັບ": "📱",
        "computer": "🖥️", "laptop": "💻", "ຄອມພິວເຕີ": "🖥️",
        "music": "🎸", "instrument": "🎹", "guitar": "🎸", "piano": "🎹", "drum": "🥁", "ເຄື່ອງດົນຕີ": "🎸", "ດົນຕີ": "🎸",
        "fashion": "👕", "clothes": "👕", "clothing": "👗", "beauty": "💄", "cosmetic": "💄",
        "food": "🍎", "drink": "🥤", "ອາຫານ": "🍎", "home": "🏠", "furniture": "🛋️",
        "sport": "⚽", "fitness": "🏋️", "book": "📚", "education": "📚", "car": "🚗", "vehicle": "🚗", "pet": "🐾",
    }
    return next((icon for keyword, icon in icons.items() if keyword in label), fallback)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    @property
    def icon(self):
        return icon_for_name(self.name)


class SubCategory(models.Model):
    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="subcategories",
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    def __str__(self):
        return f"{self.category.name} / {self.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "slug"],
                name="unique_subcategory_slug_per_category",
            )
        ]
        ordering = ["name"]


class Product(models.Model):
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(default=0)

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    video = models.FileField(
        upload_to="products/videos/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "product"
            slug = base_slug
            counter = 2
            while Product.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        return self.reviews.aggregate(value=Avg("rating"))["value"] or 0

    @property
    def fallback_icon(self):
        return icon_for_name(f"{self.name} {self.category.name}", icon_for_name(self.category.name))

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(stock__gte=0), name="product_stock_nonnegative")
        ]


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_wishlist_item")]


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_product_review"),
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name="review_rating_1_to_5"),
        ]
