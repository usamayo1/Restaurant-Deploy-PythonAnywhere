from collections import defaultdict

from django.db import migrations
from django.utils import timezone


def backfill_order_numbers(apps, schema_editor):
    Order = apps.get_model("food", "Order")

    counters = defaultdict(int)

    for order in Order.objects.order_by("created_at", "id"):
        if order.order_number:
            continue

        created_at = order.created_at or timezone.now()
        local_created_at = timezone.localtime(created_at)
        date_code = local_created_at.strftime("%Y%m%d")

        counters[date_code] += 1
        order.order_number = f"ORD-{date_code}-{counters[date_code]:03d}"
        order.save(update_fields=["order_number"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("food", "0024_order_order_number"),
    ]

    operations = [
        migrations.RunPython(backfill_order_numbers, noop_reverse),
    ]
