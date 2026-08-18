from django.db import migrations, models


def merge_duplicate_cart_items(apps, schema_editor):
    CartItem = apps.get_model("cart", "CartItem")
    duplicates = (
        CartItem.objects.values("user_id", "product_id")
        .annotate(count=models.Count("id"))
        .filter(count__gt=1)
    )
    for duplicate in duplicates:
        items = CartItem.objects.filter(
            user_id=duplicate["user_id"], product_id=duplicate["product_id"]
        ).order_by("id")
        primary = items.first()
        primary.quantity = sum(item.quantity for item in items)
        primary.save(update_fields=["quantity"])
        items.exclude(pk=primary.pk).delete()


class Migration(migrations.Migration):
    dependencies = [("cart", "0001_initial")]

    operations = [
        migrations.RunPython(merge_duplicate_cart_items, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=("user", "product"), name="unique_cart_item_per_user_product"
            ),
        ),
    ]
