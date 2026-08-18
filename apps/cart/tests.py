from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.products.models import Category, Product
from .models import CartItem


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="safe-password")
        seller = User.objects.create_user(username="seller", password="safe-password")
        category = Category.objects.create(name="Phones", slug="phones")
        self.product = Product.objects.create(
            seller=seller, category=category, name="Phone", slug="phone",
            description="A phone", price=Decimal("200.00"), stock=3,
        )
        self.client.force_login(self.user)

    def test_add_same_product_increments_one_cart_item(self):
        url = reverse("add_to_cart", args=[self.product.pk])
        self.client.post(url)
        self.client.post(url)
        item = CartItem.objects.get(user=self.user, product=self.product)
        self.assertEqual(item.quantity, 2)

    def test_add_to_cart_requires_post(self):
        response = self.client.get(reverse("add_to_cart", args=[self.product.pk]))
        self.assertEqual(response.status_code, 405)

    def test_add_single_stock_product_to_cart(self):
        self.product.stock = 1
        self.product.save()
        self.client.post(reverse("add_to_cart", args=[self.product.pk]))
        self.assertEqual(CartItem.objects.get(user=self.user, product=self.product).quantity, 1)

    def test_cart_quantity_cannot_exceed_stock(self):
        url = reverse("add_to_cart", args=[self.product.pk])
        for _ in range(4):
            self.client.post(url)

        item = CartItem.objects.get(user=self.user, product=self.product)
        self.assertEqual(item.quantity, self.product.stock)

    def test_update_to_zero_removes_cart_item(self):
        item = CartItem.objects.create(user=self.user, product=self.product, quantity=1)

        response = self.client.post(
            reverse("update_cart_item", args=[item.pk]), {"quantity": 0}
        )

        self.assertRedirects(response, reverse("cart"))
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_user_cannot_update_another_users_cart_item(self):
        other_user = User.objects.create_user(
            username="other-buyer", password="safe-password"
        )
        other_item = CartItem.objects.create(
            user=other_user, product=self.product, quantity=1
        )

        response = self.client.post(
            reverse("update_cart_item", args=[other_item.pk]), {"quantity": 2}
        )

        self.assertEqual(response.status_code, 404)
        other_item.refresh_from_db()
        self.assertEqual(other_item.quantity, 1)
