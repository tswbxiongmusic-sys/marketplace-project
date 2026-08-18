from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security)
def production_settings_check(app_configs, **kwargs):
    if not settings.IS_PRODUCTION:
        return []
    errors = []
    if len(settings.SECRET_KEY) < 50 or "replace" in settings.SECRET_KEY.lower():
        errors.append(Error("Set a strong production SECRET_KEY.", id="marketplace.E001"))
    if not settings.ALLOWED_HOSTS:
        errors.append(Error("Set ALLOWED_HOSTS for the production domain.", id="marketplace.E002"))
    if not settings.CSRF_TRUSTED_ORIGINS:
        errors.append(Error("Set CSRF_TRUSTED_ORIGINS using https://your-domain.", id="marketplace.E003"))
    return errors
