from decimal import Decimal

from django.utils import timezone

from .models import SiteSettings


def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def calculate_totals(cart, user=None):
    settings_obj = SiteSettings.objects.first() or SiteSettings()

    subtotal = sum(
        Decimal(item["price"]) * item["quantity"]
        for item in cart.values()
    )

    tax_percent = settings_obj.tax_percent or Decimal("0")
    tax = subtotal * (tax_percent / Decimal("100"))

    now = timezone.now()
    special_active = False
    special_discount_percent = Decimal("0")

    if (
        settings_obj.special_discount_percent
        and settings_obj.special_discount_start
        and settings_obj.special_discount_end
        and settings_obj.special_discount_start <= now <= settings_obj.special_discount_end
    ):
        special_active = True
        special_discount_percent = settings_obj.special_discount_percent

    auth_discount_percent = settings_obj.auth_user_discount_percent or Decimal("0")
    applied_auth_discount_percent = Decimal("0")
    if user and user.is_authenticated:
        applied_auth_discount_percent = auth_discount_percent

    discount_percent = special_discount_percent + applied_auth_discount_percent
    discount = subtotal * (discount_percent / Decimal("100"))

    free_delivery_threshold = settings_obj.free_delivery_threshold or Decimal("0")
    delivery_fee = settings_obj.delivery_fee or Decimal("0")

    if subtotal >= free_delivery_threshold:
        delivery = Decimal("0.00")
        delivery_saved = delivery_fee
        free_delivery_qualified = True
    else:
        delivery = delivery_fee
        delivery_saved = Decimal("0.00")
        free_delivery_qualified = False

    amount_needed_for_free_delivery = max(
        Decimal("0.00"),
        free_delivery_threshold - subtotal,
    )

    total_saved = discount + delivery_saved
    total = subtotal + tax + delivery - discount

    return {
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "tax_percent": tax_percent,
        "discount": round(discount, 2),
        "discount_percent": discount_percent,
        "delivery": round(delivery, 2),
        "total": round(total, 2),
        "you_saved": round(total_saved, 2),
        "delivery_saved": round(delivery_saved, 2),
        "free_delivery_threshold": free_delivery_threshold,
        "amount_needed_for_free_delivery": round(amount_needed_for_free_delivery, 2),
        "free_delivery_qualified": free_delivery_qualified,
        "auth_discount_percent": auth_discount_percent,
        "special_discount_percent": special_discount_percent,
        "special_discount_end": settings_obj.special_discount_end,
        "special_active": special_active,
    }


def get_staff_unread_chat_counts(seen_map=None):
    from .models import LiveChatMessage

    seen_map = seen_map or {}
    seen_by_thread = {}
    for key, value in seen_map.items():
        try:
            seen_by_thread[int(key)] = int(value)
        except (TypeError, ValueError):
            continue

    unread_per_thread = {}
    customer_messages = (
        LiveChatMessage.objects
        .filter(sender_type=LiveChatMessage.SENDER_CUSTOMER)
        .values_list("thread_id", "id")
        .order_by("id")
    )

    for thread_id, message_id in customer_messages:
        seen_id = seen_by_thread.get(int(thread_id), 0)
        if message_id <= seen_id:
            continue
        unread_per_thread[thread_id] = unread_per_thread.get(thread_id, 0) + 1

    return {
        "threads": len(unread_per_thread),
        "messages": sum(unread_per_thread.values()),
    }
