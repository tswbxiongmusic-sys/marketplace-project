from django.apps import AppConfig
from types import MethodType


APP_LABELS = {
    "accounts": "ຜູ້ໃຊ້ ແລະ ບັນຊີ",
    "cart": "ກະຕ່າສິນຄ້າ",
    "core": "ລະບົບຮ້ານ",
    "orders": "ຄຳສັ່ງຊື້",
    "products": "ສິນຄ້າ",
    "auth": "ສິດທິ ແລະ ກຸ່ມ",
}

MODEL_LABELS = {
    "accounts.User": "ຜູ້ໃຊ້",
    "accounts.Notification": "ການແຈ້ງເຕືອນ",
    "cart.CartItem": "ລາຍການໃນກະຕ່າ",
    "core.StoreSettings": "ຂໍ້ມູນຮ້ານ",
    "orders.Order": "ຄຳສັ່ງຊື້",
    "products.Category": "ໝວດໝູ່",
    "products.SubCategory": "ໝວດຍ່ອຍ",
    "products.Product": "ສິນຄ້າ",
    "products.ProductImage": "ຮູບສິນຄ້າ",
    "products.Review": "ຣີວິວ",
    "products.Wishlist": "ລາຍການທີ່ມັກ",
    "auth.Group": "ກຸ່ມ",
}


def get_lao_app_list(site, request, app_label=None):
    """Translate the app and model names shown on the Django admin home page."""
    app_list = site._marketplace_original_get_app_list(request, app_label)
    for app in app_list:
        app["name"] = APP_LABELS.get(app["app_label"], app["name"])
        for model in app["models"]:
            key = f"{app['app_label']}.{model['object_name']}"
            model["name"] = MODEL_LABELS.get(key, model["name"])
    return app_list


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.core"
    verbose_name = "ລະບົບຮ້ານ"

    def ready(self):
        from . import checks  # noqa: F401
        from django.contrib import admin

        admin.site.site_header = "ລະບົບຈັດການຮ້ານ"
        admin.site.site_title = "ຈັດການຮ້ານ"
        admin.site.index_title = "ໜ້າຈັດການ"
        if not hasattr(admin.site, "_marketplace_original_get_app_list"):
            admin.site._marketplace_original_get_app_list = admin.site.get_app_list
            admin.site.get_app_list = MethodType(get_lao_app_list, admin.site)
