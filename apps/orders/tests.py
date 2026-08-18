from decimal import Decimal
from io import BytesIO
import tempfile

from django.test import TestCase
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.models import Notification
from apps.cart.models import CartItem
from apps.products.models import Category, Product
from .models import Order, OrderItem, OrderShipment, ShippingMethod


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="safe-password")
        self.seller = User.objects.create_user(
            username="seller",
            password="safe-password",
            role=User.Role.SELLER,
        )
        self.other_seller = User.objects.create_user(
            username="other-seller",
            password="safe-password",
            role=User.Role.SELLER,
        )
        self.shipping_method = ShippingMethod.objects.create(
            name="ສົ່ງທົ່ວໄປ",
            fee=Decimal("20000.00"),
            estimated_delivery="2-5 ມື້",
        )
        category = Category.objects.create(name="Phones", slug="phones")
        self.product = Product.objects.create(
            seller=self.seller, category=category, name="Phone", slug="phone",
            description="A phone", price=Decimal("200.00"), stock=2,
        )
        self.client.force_login(self.user)

    def test_checkout_creates_order_and_reduces_stock(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=2)
        response = self.client.post(
            reverse("place_order"),
            data={
                "recipient_name": "Buyer",
                "phone": "020000000",
                "shipping_address": "Laos",
                "shipping_method": self.shipping_method.pk,
                "payment_method": "cash_on_delivery",
            },
        )
        self.assertRedirects(response, reverse("my_orders"))
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)
        self.assertFalse(CartItem.objects.exists())
        order = Order.objects.get()
        self.assertTrue(order.order_number.startswith("ORD-"))
        self.assertEqual(order.shipping_method, self.shipping_method)
        self.assertEqual(order.shipping_fee, Decimal("20000.00"))
        self.assertEqual(order.total_price, Decimal("20400.00"))
        shipment = OrderShipment.objects.get(order=order)
        self.assertEqual(shipment.seller, self.seller)
        self.assertEqual(shipment.status, "pending")

    def test_checkout_lists_active_shipping_methods(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.shipping_method.name)

    def test_checkout_keeps_cart_when_stock_is_insufficient(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=3)
        self.client.post(
            reverse("place_order"),
            data={
                "recipient_name": "Buyer",
                "phone": "020000000",
                "shipping_address": "Laos",
                "shipping_method": self.shipping_method.pk,
                "payment_method": "cash_on_delivery",
            },
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertTrue(CartItem.objects.exists())

    def test_qr_payment_requires_a_transfer_receipt(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)

        response = self.client.post(
            reverse("place_order"),
            data={
                "recipient_name": "Buyer",
                "phone": "020000000",
                "shipping_address": "Laos",
                "shipping_method": self.shipping_method.pk,
                "payment_method": "qr_payment",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ກະລຸນາອັບໂຫຼດຫຼັກຖານ")
        self.assertFalse(Order.objects.exists())
        self.assertTrue(CartItem.objects.exists())

    def test_bank_transfer_requires_a_transfer_receipt(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)

        response = self.client.post(
            reverse("place_order"),
            data={
                "recipient_name": "Buyer",
                "phone": "020000000",
                "shipping_address": "Laos",
                "shipping_method": self.shipping_method.pk,
                "payment_method": "bank_transfer",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ກະລຸນາອັບໂຫຼດຫຼັກຖານ")
        self.assertFalse(Order.objects.exists())

    def test_qr_payment_stores_receipt_and_starts_pending_review(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), "white").save(image_buffer, format="PNG")
        receipt = SimpleUploadedFile(
            "receipt.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("place_order"),
                data={
                    "recipient_name": "Buyer",
                    "phone": "020000000",
                    "shipping_address": "Laos",
                    "shipping_method": self.shipping_method.pk,
                    "payment_method": "qr_payment",
                    "payment_receipt": receipt,
                },
            )

        self.assertRedirects(response, reverse("my_orders"))
        order = Order.objects.get()
        self.assertEqual(order.payment_method, "qr_payment")
        self.assertEqual(order.payment_status, "pending")
        self.assertTrue(order.payment_receipt.name)

    def test_order_detail_shows_order_information(self):
        order = Order.objects.create(
            user=self.user,
            recipient_name="Buyer",
            phone="020000000",
            shipping_address="Laos",
            shipping_method=self.shipping_method,
            shipping_fee=Decimal("20000.00"),
            payment_method="cash_on_delivery",
            payment_status="pending",
            total_price=Decimal("20400.00"),
            status="pending",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=2,
            total_price=self.product.price * 2,
        )

        response = self.client.get(reverse("order_detail", args=[order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.recipient_name)
        self.assertContains(response, self.product.name)

    def test_order_detail_is_restricted_to_order_owner(self):
        other_user = User.objects.create_user(username="other", password="safe-password")
        other_order = Order.objects.create(
            user=other_user,
            recipient_name="Other Buyer",
            phone="020000001",
            shipping_address="Vientiane",
            payment_method="cash_on_delivery",
            payment_status="pending",
            total_price=Decimal("200.00"),
            status="pending",
        )

        response = self.client.get(reverse("order_detail", args=[other_order.id]))
        self.assertEqual(response.status_code, 404)

    def test_pending_order_cancellation_restores_stock(self):
        order = Order.objects.create(user=self.user, recipient_name="Buyer", phone="020", shipping_address="Laos", total_price="200.00")
        OrderItem.objects.create(order=order, product=self.product, product_name="Phone", unit_price="200.00", quantity=1, total_price="200.00")
        self.product.stock = 1
        self.product.save()
        self.client.post(reverse("cancel_order", args=[order.pk]))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(self.product.stock, 2)

    def test_seller_updates_only_own_shipment_and_tracking(self):
        order = Order.objects.create(
            user=self.user,
            recipient_name="Buyer",
            phone="020000000",
            shipping_address="Laos",
            shipping_method=self.shipping_method,
            shipping_fee=self.shipping_method.fee,
            total_price=Decimal("20200.00"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=1,
            total_price=self.product.price,
        )
        shipment = OrderShipment.objects.create(order=order, seller=self.seller)

        self.client.force_login(self.other_seller)
        response = self.client.post(
            reverse("update_shipment_status", args=[shipment.pk]),
            {"status": "shipping", "carrier": "Post", "tracking_number": "TRACK-123"},
        )
        self.assertEqual(response.status_code, 404)
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, "pending")

        self.client.force_login(self.seller)
        response = self.client.post(
            reverse("update_shipment_status", args=[shipment.pk]),
            {"status": "shipping", "carrier": "Post", "tracking_number": "TRACK-123"},
        )
        self.assertRedirects(response, reverse("seller_orders"))
        shipment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(shipment.status, "shipping")
        self.assertEqual(shipment.carrier, "Post")
        self.assertEqual(shipment.tracking_number, "TRACK-123")
        self.assertIsNotNone(shipment.shipped_at)
        self.assertEqual(order.status, "shipping")

        response = self.client.get(reverse("seller_orders"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TRACK-123")

        self.client.post(
            reverse("update_shipment_status", args=[shipment.pk]),
            {"status": "delivered", "carrier": "Post", "tracking_number": "TRACK-123"},
        )
        shipment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(shipment.status, "delivered")
        self.assertIsNotNone(shipment.delivered_at)
        self.assertEqual(order.status, "completed")

    def test_seller_cannot_ship_unverified_qr_payment(self):
        order = Order.objects.create(
            user=self.user,
            recipient_name="Buyer",
            phone="020000000",
            shipping_address="Laos",
            shipping_method=self.shipping_method,
            shipping_fee=self.shipping_method.fee,
            payment_method="qr_payment",
            payment_status="pending",
            total_price=Decimal("20200.00"),
        )
        shipment = OrderShipment.objects.create(order=order, seller=self.seller)
        self.client.force_login(self.seller)

        response = self.client.post(
            reverse("update_shipment_status", args=[shipment.pk]),
            {"status": "shipping", "carrier": "Post", "tracking_number": "QR-123"},
        )

        self.assertRedirects(response, reverse("seller_orders"))
        shipment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(shipment.status, "pending")
        self.assertEqual(order.status, "pending")

        order.payment_status = "paid"
        order.status = "paid"
        order.save(update_fields=["payment_status", "status"])
        response = self.client.post(
            reverse("update_shipment_status", args=[shipment.pk]),
            {"status": "shipping", "carrier": "Post", "tracking_number": "QR-123"},
        )

        self.assertRedirects(response, reverse("seller_orders"))
        shipment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(shipment.status, "shipping")
        self.assertEqual(order.status, "shipping")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_admin_can_confirm_payment_and_notify_buyer(self):
        order = Order.objects.create(
            user=self.user,
            recipient_name="Buyer",
            phone="020000000",
            shipping_address="Laos",
            payment_method="qr_payment",
            payment_status="pending",
            status="pending",
            total_price=Decimal("200.00"),
        )
        admin_user = User.objects.create_superuser(
            username="admin-user",
            email="admin@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(admin_user)

        response = self.client.post(
            reverse("admin:orders_order_changelist"),
            {"action": "mark_as_paid", "_selected_action": [str(order.pk)]},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(order.status, "paid")
        self.assertTrue(Notification.objects.filter(user=self.user).exists())

    def test_completed_order_cannot_be_cancelled(self):
        order = Order.objects.create(user=self.user, recipient_name="Buyer", phone="020", shipping_address="Laos", total_price="200.00", status="completed")
        self.client.post(reverse("cancel_order", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, "completed")
