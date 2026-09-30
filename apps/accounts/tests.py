from types import SimpleNamespace

from django import forms
from django.conf import settings
from django.test import TestCase, override_settings
from django.template.loader import get_template
from django.urls import reverse

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialApp

from .models import User
from .social_account_adapter import MarketplaceSocialAccountAdapter


class AccountTests(TestCase):
    def test_registration_creates_and_logs_in_user(self):
        response = self.client.post(reverse("register"), {
            "username": "newbuyer", "email": "tswbxiongmusi@gmail.com", "phone": "02056095785",
            "password1": "A-safe-password123", "password2": "A-safe-password123",
        })
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.filter(username="newbuyer").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_social_signup_template_uses_lao_completion_page(self):
        class SocialAccountStub:
            def get_provider(self):
                return SimpleNamespace(id="google", name="Google")

        form = forms.Form()
        form.fields["username"] = forms.CharField()
        form.fields["email"] = forms.EmailField()
        html = get_template("socialaccount/signup.html").render(
            {
                "account": SocialAccountStub(),
                "form": form,
                "store": SimpleNamespace(name="ຕະຫຼາດອອນລາຍ"),
                "redirect_field": "",
            }
        )

        self.assertIn("ເກືອບສຳເລັດແລ້ວ", html)
        self.assertIn("ບໍ່ຕ້ອງສ້າງ ຫຼື ຈື່ລະຫັດຜ່ານ", html)

    @override_settings(
        GOOGLE_LOGIN_ENABLED=True,
        FACEBOOK_LOGIN_ENABLED=True,
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "APP": {"client_id": "google-id", "secret": "google-secret", "key": ""},
                "SCOPE": ["profile", "email"],
            },
            "facebook": {
                "APP": {"client_id": "facebook-id", "secret": "facebook-secret", "key": ""},
                "METHOD": "oauth2",
                "SCOPE": ["email", "public_profile"],
            },
        },
    )
    def test_login_page_shows_enabled_social_sign_in_providers(self):
        for page_name in ("login", "register"):
            response = self.client.get(reverse(page_name))

            self.assertContains(response, "ສືບຕໍ່ດ້ວຍ Google")
            self.assertContains(response, "ສືບຕໍ່ດ້ວຍ Facebook")
            self.assertContains(response, 'action="/social/google/login/?process=login"')
            self.assertContains(response, 'action="/social/facebook/login/?process=login"')

        for login_path, provider_host in (
            ("/social/google/login/?process=login", "accounts.google.com"),
            ("/social/facebook/login/?process=login", "facebook.com"),
        ):
            response = self.client.post(login_path)

            self.assertEqual(response.status_code, 302)
            self.assertIn(provider_host, response["Location"])

    @override_settings(GOOGLE_LOGIN_ENABLED=True)
    def test_login_page_uses_the_forest_glass_design(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, 'class="auth-forest-page"')
        self.assertContains(response, 'class="auth-forest-scene"')
        self.assertContains(response, "ຫຼື ເຂົ້າດ້ວຍ")

    def test_verified_google_email_links_to_an_existing_user(self):
        user = User.objects.create_user(
            username="existingbuyer",
            email="buyer@example.com",
            password="A-safe-password123",
        )
        social_login = SimpleNamespace(
            provider=SimpleNamespace(
                app=None,
                get_settings=lambda: {"EMAIL_AUTHENTICATION": True},
            ),
            email_addresses=[EmailAddress(email=user.email, verified=True)],
        )

        authenticated = MarketplaceSocialAccountAdapter().authenticate_by_email(
            social_login
        )

        self.assertEqual(authenticated, (user, user.email))
        self.assertTrue(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT)

    def test_unverified_social_email_cannot_link_to_an_existing_user(self):
        user = User.objects.create_user(
            username="protectedbuyer",
            email="protected@example.com",
            password="A-safe-password123",
        )
        social_login = SimpleNamespace(
            provider=SimpleNamespace(
                app=None,
                get_settings=lambda: {"EMAIL_AUTHENTICATION": True},
            ),
            email_addresses=[EmailAddress(email=user.email, verified=False)],
        )

        authenticated = MarketplaceSocialAccountAdapter().authenticate_by_email(
            social_login
        )

        self.assertIsNone(authenticated)

    @override_settings(
        GOOGLE_LOGIN_ENABLED=True,
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "APP": {"client_id": "google-id", "secret": "google-secret", "key": ""},
                "SCOPE": ["profile", "email"],
            },
        },
    )
    def test_environment_google_app_wins_over_legacy_admin_app(self):
        legacy_app = SocialApp.objects.create(
            provider="google",
            name="Legacy Google Login",
            client_id="legacy-google-id",
            secret="legacy-google-secret",
        )
        legacy_app.sites.add(legacy_app.sites.model.objects.get_current())

        response = self.client.post("/social/google/login/?process=login")

        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])

    @override_settings(GOOGLE_LOGIN_ENABLED=False, FACEBOOK_LOGIN_ENABLED=False)
    def test_login_page_hides_unconfigured_social_sign_in_providers(self):
        response = self.client.get(reverse("login"))

        self.assertNotContains(response, "ສືບຕໍ່ດ້ວຍ Google")
        self.assertNotContains(response, "ສືບຕໍ່ດ້ວຍ Facebook")


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("resetme", "resetme@example.com", "Old-password-123")

    def test_login_page_links_to_password_reset(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("password_reset"))

    def test_reset_flow_emails_link_on_request_host_and_sets_new_password(self):
        from django.core import mail

        response = self.client.post(
            reverse("password_reset"), {"email": "resetme@example.com"}, HTTP_HOST="127.0.0.1:8000"
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn("http://127.0.0.1:8000/accounts/password-reset/", body)
        self.assertNotIn("example.com/accounts", body)

        link = next(line for line in body.splitlines() if "/password-reset/" in line).strip()
        path = link.split("127.0.0.1:8000", 1)[1]
        response = self.client.get(path, follow=True)
        self.assertContains(response, "ຕັ້ງລະຫັດຜ່ານໃໝ່")
        response = self.client.post(
            response.redirect_chain[-1][0],
            {"new_password1": "Brand-new-pass-456", "new_password2": "Brand-new-pass-456"},
        )
        self.assertRedirects(response, reverse("password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Brand-new-pass-456"))

    def test_unknown_email_shows_same_done_page_without_sending(self):
        from django.core import mail

        response = self.client.post(reverse("password_reset"), {"email": "nobody@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_token_shows_expired_message(self):
        response = self.client.get(
            reverse("password_reset_confirm", kwargs={"uidb64": "xx", "token": "bad-token"})
        )
        self.assertContains(response, "ລິ້ງໃຊ້ບໍ່ໄດ້")


@override_settings(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_BOT_USERNAME="HmongShopBot")
class TelegramLinkTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("tg-seller", password="x-Strong-pass-1", role=User.Role.SELLER)
        self.client.force_login(self.seller)

    def test_connect_issues_token_and_redirects_to_bot(self):
        response = self.client.post(reverse("telegram_connect"))
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.telegram_link_token)
        self.assertEqual(response.url, f"https://t.me/HmongShopBot?start={self.seller.telegram_link_token}")

    def test_verify_links_chat_from_start_message_and_acknowledges_updates(self):
        from unittest import mock

        self.seller.telegram_link_token = "tok123"
        self.seller.save()
        updates = [
            {"update_id": 7, "message": {"text": "/start unknown", "chat": {"id": 1}}},
            {"update_id": 8, "message": {"text": "/start tok123", "chat": {"id": 555}}},
        ]
        calls = []

        def fake_call(method, **params):
            calls.append((method, params))
            return updates if method == "getUpdates" and "offset" not in params else True

        with mock.patch("apps.accounts.telegram._call", side_effect=fake_call):
            self.client.post(reverse("telegram_verify"))
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.telegram_chat_id, "555")
        self.assertEqual(self.seller.telegram_link_token, "")
        self.assertIn(("getUpdates", {"offset": 9, "timeout": 0}), calls)

    def test_disconnect_clears_chat(self):
        self.seller.telegram_chat_id = "555"
        self.seller.save()
        self.client.post(reverse("telegram_disconnect"))
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.telegram_chat_id, "")

    def test_dashboard_shows_card_only_when_bot_configured(self):
        self.assertContains(self.client.get(reverse("seller_dashboard")), "telegram-alerts")
        with self.settings(TELEGRAM_BOT_TOKEN=""):
            self.assertNotContains(self.client.get(reverse("seller_dashboard")), "telegram-alerts")

    def test_customers_cannot_connect(self):
        customer = User.objects.create_user("tg-buyer", password="x-Strong-pass-1")
        self.client.force_login(customer)
        self.client.post(reverse("telegram_connect"))
        customer.refresh_from_db()
        self.assertEqual(customer.telegram_link_token, "")
