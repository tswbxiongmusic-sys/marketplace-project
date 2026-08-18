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
