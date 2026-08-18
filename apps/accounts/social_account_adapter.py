"""Social-account behavior specific to this marketplace."""

import logging

from django.conf import settings

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


logger = logging.getLogger(__name__)


class MarketplaceSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Prefer the secret-environment OAuth app over old admin records.

    OAuth credentials for Google and Facebook are deliberately configured from
    environment variables in this project. Older SocialApp records may still
    exist in the database from an earlier setup. django-allauth normally merges
    both sources and raises ``MultipleObjectsReturned``. When an environment
    app is configured, retain only that unsaved, settings-backed app.
    """

    def list_apps(self, request, provider=None, client_id=None):
        apps = super().list_apps(request, provider=provider, client_id=client_id)
        provider_settings = settings.SOCIALACCOUNT_PROVIDERS.get(provider or "", {})

        if provider_settings.get("APP"):
            return [app for app in apps if app.pk is None]

        return apps

    def on_authentication_error(
        self,
        request,
        provider,
        error=None,
        exception=None,
        extra_context=None,
    ):
        """Log a safe diagnostic for local OAuth callback failures.

        Client secrets and OAuth tokens are deliberately excluded from the log.
        """
        logger.warning(
            "Social login failed: provider=%s error=%s exception_type=%s",
            getattr(provider, "id", "unknown"),
            error,
            type(exception).__name__ if exception else "none",
        )
        return super().on_authentication_error(
            request,
            provider,
            error=error,
            exception=exception,
            extra_context=extra_context,
        )
