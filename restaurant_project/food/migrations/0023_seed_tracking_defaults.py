from datetime import timedelta

from django.db import migrations
from django.utils import timezone


DEFAULT_MESSAGES = {
    "pending": "Your order has been received and is waiting for confirmation.",
    "confirmed": "Your order is confirmed and queued in the kitchen.",
    "preparing": "Our kitchen is preparing your food right now.",
    "out_for_delivery": "Your order is out for delivery.",
    "delivered": "Your order has been delivered. Enjoy your meal.",
    "cancelled": "This order has been cancelled.",
}


def seed_tracking_defaults(apps, schema_editor):
    Order = apps.get_model("food", "Order")
    OrderStatusAutomationRule = apps.get_model("food", "OrderStatusAutomationRule")
    OrderStatusHistory = apps.get_model("food", "OrderStatusHistory")

    default_rules = [
        {
            "from_status": "pending",
            "to_status": "confirmed",
            "delay_minutes": 2,
            "customer_message": "Your order has been confirmed by the restaurant.",
            "admin_note": "Auto-confirm new orders after review delay.",
        },
        {
            "from_status": "confirmed",
            "to_status": "preparing",
            "delay_minutes": 8,
            "customer_message": "Our kitchen has started preparing your order.",
            "admin_note": "Move confirmed orders into kitchen preparation.",
        },
        {
            "from_status": "preparing",
            "to_status": "out_for_delivery",
            "delay_minutes": 20,
            "customer_message": "Your order has left the kitchen and is now on the way.",
            "admin_note": "Dispatch prepared orders for delivery.",
        },
        {
            "from_status": "out_for_delivery",
            "to_status": "delivered",
            "delay_minutes": 25,
            "customer_message": "Your order was marked delivered. Enjoy your meal.",
            "admin_note": "Automatically complete delivered trips after ETA.",
        },
    ]

    for rule in default_rules:
        OrderStatusAutomationRule.objects.get_or_create(
            from_status=rule["from_status"],
            defaults=rule,
        )

    active_rules = {
        rule.from_status: rule
        for rule in OrderStatusAutomationRule.objects.filter(is_active=True)
    }

    for order in Order.objects.all():
        base_time = order.status_updated_at or order.created_at or timezone.now()
        next_auto_status_at = None

        if order.status not in {"delivered", "cancelled"}:
            rule = active_rules.get(order.status)
            if rule:
                next_auto_status_at = base_time + timedelta(minutes=rule.delay_minutes)

        delivered_at = order.delivered_at
        if order.status == "delivered" and not delivered_at:
            delivered_at = base_time
        if order.status != "delivered":
            delivered_at = None

        Order.objects.filter(pk=order.pk).update(
            status_updated_at=base_time,
            next_auto_status_at=next_auto_status_at,
            delivered_at=delivered_at,
        )

        if not OrderStatusHistory.objects.filter(order=order).exists():
            OrderStatusHistory.objects.create(
                order=order,
                previous_status="",
                status=order.status,
                is_automatic=False,
                note="Tracking initialized for existing order.",
                customer_message=DEFAULT_MESSAGES.get(order.status, "Your order is being processed."),
                changed_at=base_time,
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("food", "0022_orderstatusautomationrule_order_delivered_at_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_tracking_defaults, noop_reverse),
    ]
