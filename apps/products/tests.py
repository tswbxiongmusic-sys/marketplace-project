from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.products.models import Category, Product, SubCategory


class CategorySubcategoryModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="seller1",
            email="seller@example.com",
            password="StrongPass123!",
        )
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.subcategory = SubCategory.objects.create(
            category=self.category,
            name="Smartphones",
            slug="smartphones",
        )
        self.product = Product.objects.create(
            seller=self.user,
            category=self.category,
            subcategory=self.subcategory,
            name="Galaxy A55",
            slug="galaxy-a55",
            description="A mid-range phone.",
            price="299.99",
            stock=12,
        )

    def test_subcategory_belongs_to_category(self):
        self.assertEqual(self.subcategory.category, self.category)
        self.assertIn(self.subcategory, self.category.subcategories.all())

    def test_product_can_be_filtered_by_subcategory(self):
        queryset = Product.objects.filter(subcategory=self.subcategory)
        self.assertIn(self.product, queryset)
        self.assertEqual(queryset.count(), 1)

    def test_product_slug_is_generated_and_unique(self):
        second = Product.objects.create(
            seller=self.user, category=self.category, name="Galaxy A55", description="Another", price="10.00", stock=1
        )
        self.assertEqual(second.slug, "galaxy-a55-2")

    def test_customer_cannot_open_seller_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("seller_dashboard"))
        self.assertRedirects(response, reverse("home"))

    def test_customer_cannot_create_product(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("add_product"),
            {
                "name": "Customer product",
                "category": self.category.pk,
                "description": "Must not be created.",
                "price": "10.00",
                "stock": 1,
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Product.objects.filter(name="Customer product").exists())

    def test_seller_can_create_a_product_for_own_store(self):
        seller = get_user_model().objects.create_user(
            username="seller2",
            email="seller2@example.com",
            password="StrongPass123!",
            role=get_user_model().Role.SELLER,
        )
        self.client.force_login(seller)

        response = self.client.post(
            reverse("add_product"),
            {
                "name": "Seller product",
                "category": self.category.pk,
                "description": "Created by the seller.",
                "price": "25.00",
                "stock": 4,
            },
        )

        self.assertRedirects(response, reverse("seller_dashboard"))
        product = Product.objects.get(name="Seller product")
        self.assertEqual(product.seller, seller)
        self.assertEqual(product.slug, "seller-product")

    def test_seller_cannot_archive_another_sellers_product(self):
        other_seller = get_user_model().objects.create_user(
            username="seller3",
            email="seller3@example.com",
            password="StrongPass123!",
            role=get_user_model().Role.SELLER,
        )
        self.client.force_login(other_seller)

        response = self.client.post(reverse("archive_product", args=[self.product.pk]))

        self.assertEqual(response.status_code, 404)
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_active)
