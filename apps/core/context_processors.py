from django.conf import settings

from apps.cart.models import CartItem
from .models import StoreSettings


def cart_count(request):
    # The admin keeps this as a singleton, but its primary key is not
    # guaranteed to be 1 after imports or restored backups.
    store = StoreSettings.objects.order_by("pk").first()
    if store is None:
        store = StoreSettings.objects.create()
    context = {
        "cart_count": 0,
        "unread_notifications": 0,
        "store": store,
        "social_login_providers": {
            "google": getattr(settings, "GOOGLE_LOGIN_ENABLED", False),
            "facebook": getattr(settings, "FACEBOOK_LOGIN_ENABLED", False),
        },
    }
    if not request.user.is_authenticated:
        return context

    context.update(
        {
            "cart_count": CartItem.objects.filter(user=request.user).count(),
            "unread_notifications": request.user.notifications.filter(is_read=False).count(),
        }
    )
    return context
