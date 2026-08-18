from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.products.models import Category, Product

from .models import StoreSettings


class StorefrontLocalizationTests(TestCase):
    def setUp(self):
        self.store = StoreSettings.objects.create(
            name="ຮ້ານທົດສອບ",
            tagline="ຮ້ານຄຸນນະພາບ",
            phone="020 5555 5555",
            email="shop@example.com",
            address="ນະຄອນຫຼວງວຽງຈັນ",
        )
        self.seller = get_user_model().objects.create_user(
            username="seller",
            password="safe-password",
            role="SELLER",
        )
        category = Category.objects.create(name="ສິນຄ້າທົດສອບ", slug="test-category")
        Product.objects.create(
            seller=self.seller,
            category=category,
            name="ສິນຄ້າທົດສອບ",
            description="ລາຍລະອຽດ",
            price="10.00",
            stock=2,
        )

    def test_store_info_uses_store_settings(self):
        response = self.client.get(reverse("store_info"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.store.name)
        self.assertContains(response, "ຂໍ້ມູນຕິດຕໍ່")

    def test_store_policies_page_is_available(self):
        response = self.client.get(reverse("store_policies"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ນະໂຍບາຍຮ້ານ")
        self.assertContains(response, "ການຈັດສົ່ງ")

    def test_seller_dashboard_uses_lao_copy(self):
        self.client.force_login(self.seller)
        response = self.client.get(reverse("seller_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ໜ້າຈັດການຮ້ານ")
        self.assertContains(response, "ສິນຄ້າຂອງຂ້ອຍ")

    def test_admin_index_uses_lao_branding(self):
        administrator = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="safe-password",
        )
        self.client.force_login(administrator)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ລະບົບຈັດການຮ້ານ")
        self.assertContains(response, "ຜູ້ໃຊ້ ແລະ ບັນຊີ")
        self.assertContains(response, "ສິນຄ້າ")
        self.assertContains(response, "ຄຳສັ່ງຊື້")
        self.assertContains(response, "ຂໍ້ມູນຮ້ານ")

    def test_admin_management_pages_render(self):
        administrator = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="safe-password",
        )
        self.client.force_login(administrator)

        for url_name in (
            "admin:accounts_user_changelist",
            "admin:core_storesettings_changelist",
            "admin:products_product_changelist",
            "admin:orders_order_changelist",
            "admin:cart_cartitem_changelist",
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
