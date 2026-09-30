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


class ModerationAndSuspensionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.seller = User.objects.create_user(
            username="mod-seller", password="StrongPass123!", role=User.Role.SELLER
        )
        self.buyer = User.objects.create_user(username="mod-buyer", password="StrongPass123!")
        self.admin = User.objects.create_superuser("mod-admin", "admin@example.com", "StrongPass123!")
        self.category = Category.objects.create(name="Bags", slug="bags")

    def make_product(self, name, status=Product.APPROVED):
        return Product.objects.create(
            seller=self.seller, category=self.category, name=name, slug=name.lower(),
            description="d", price="100.00", stock=5, approval_status=status,
        )

    def test_only_approved_products_are_published(self):
        approved = self.make_product("Approved")
        pending = self.make_product("Pending", Product.PENDING)
        rejected = self.make_product("Rejected", Product.REJECTED)
        published = list(Product.objects.published())
        self.assertIn(approved, published)
        self.assertNotIn(pending, published)
        self.assertNotIn(rejected, published)

    def test_pending_product_is_hidden_from_buyers_but_visible_to_its_seller(self):
        pending = self.make_product("Hidden", Product.PENDING)
        url = reverse("product_detail", args=[pending.pk])

        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertNotContains(self.client.get(reverse("product_list")), "Hidden")

        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_suspended_seller_products_disappear_and_cannot_be_added_to_cart(self):
        product = self.make_product("Suspended")
        self.seller.is_suspended = True
        self.seller.save()

        self.assertNotIn(product, Product.objects.published())
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("product_detail", args=[product.pk])).status_code, 404)
        self.client.post(reverse("add_to_cart", args=[product.pk]))
        from apps.cart.models import CartItem
        self.assertFalse(CartItem.objects.filter(user=self.buyer).exists())

    def test_suspended_seller_cannot_add_or_edit_products(self):
        product = self.make_product("Mine")
        self.seller.is_suspended = True
        self.seller.save()
        self.client.force_login(self.seller)

        response = self.client.post(reverse("add_product"), {
            "name": "New", "category": self.category.pk, "description": "d", "price": "10", "stock": 1,
        })
        self.assertRedirects(response, reverse("seller_dashboard"), fetch_redirect_response=False)
        self.assertFalse(Product.objects.filter(name="New").exists())

        response = self.client.post(reverse("edit_product", args=[product.pk]), {
            "name": "Renamed", "category": self.category.pk, "description": "d", "price": "10", "stock": 1,
        })
        self.assertRedirects(response, reverse("seller_dashboard"), fetch_redirect_response=False)
        product.refresh_from_db()
        self.assertEqual(product.name, "Mine")

    def test_new_seller_product_starts_pending(self):
        self.client.force_login(self.seller)
        self.client.post(reverse("add_product"), {
            "name": "Fresh", "category": self.category.pk, "description": "d", "price": "10", "stock": 1,
        })
        self.assertEqual(Product.objects.get(name="Fresh").approval_status, Product.PENDING)

    def test_admin_approve_and_reject_actions_update_status_and_notify_seller(self):
        pending = self.make_product("ToApprove", Product.PENDING)
        other = self.make_product("ToReject", Product.PENDING)
        self.client.force_login(self.admin)
        changelist = reverse("admin:products_product_changelist")

        self.client.post(changelist, {"action": "approve_products", "_selected_action": [pending.pk]})
        self.client.post(changelist, {"action": "reject_products", "_selected_action": [other.pk]})

        pending.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(pending.approval_status, Product.APPROVED)
        self.assertEqual(pending.reviewed_by, self.admin)
        self.assertEqual(other.approval_status, Product.REJECTED)
        self.assertEqual(self.seller.notifications.count(), 2)


class SellerEditReviewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.seller = User.objects.create_user(
            username="edit-seller", password="StrongPass123!", role=User.Role.SELLER
        )
        self.category = Category.objects.create(name="Shoes", slug="shoes")
        self.product = Product.objects.create(
            seller=self.seller, category=self.category, name="Runner", slug="runner",
            description="Light shoe", price="100.00", stock=5, approval_status=Product.APPROVED,
        )
        self.client.force_login(self.seller)

    def edit(self, **changes):
        data = {
            "name": "Runner", "category": self.category.pk, "subcategory": "",
            "description": "Light shoe", "price": "100.00", "stock": 5, **changes,
        }
        response = self.client.post(reverse("edit_product", args=[self.product.pk]), data)
        self.product.refresh_from_db()
        return response

    def test_price_and_stock_changes_stay_live(self):
        self.edit(price="79.50", stock=20)
        self.assertEqual(str(self.product.price), "79.50")
        self.assertEqual(self.product.stock, 20)
        self.assertEqual(self.product.approval_status, Product.APPROVED)

    def test_changing_name_or_description_sends_product_back_to_review(self):
        self.edit(name="Totally different item")
        self.assertEqual(self.product.approval_status, Product.PENDING)
        self.assertNotIn(self.product, Product.objects.published())

        self.product.approval_status = Product.APPROVED
        self.product.save()
        self.edit(name="Totally different item", description="New text")
        self.assertEqual(self.product.approval_status, Product.PENDING)

    def test_editing_a_rejected_product_resubmits_it(self):
        self.product.approval_status = Product.REJECTED
        self.product.rejection_reason = "Bad photo"
        self.product.save()
        self.edit(price="90.00")
        self.assertEqual(self.product.approval_status, Product.PENDING)
        self.assertEqual(self.product.rejection_reason, "")

    def test_seller_cannot_edit_another_sellers_product(self):
        User = get_user_model()
        other = User.objects.create_user(username="other-s", password="StrongPass123!", role=User.Role.SELLER)
        self.client.force_login(other)
        response = self.edit(price="1.00")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(str(self.product.price), "100.00")
