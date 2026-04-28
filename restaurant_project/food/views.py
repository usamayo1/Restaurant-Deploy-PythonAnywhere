import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import FeedbackForm
from .models import (
    Category,
    DailyDeal,
    Feedback,
    HeroImage,
    ItemVariant,
    LiveChatMessage,
    LiveChatThread,
    Order,
    OrderItem,
    OurSpecial,
    PopularDeal,
    PopularDealsSection,
    SiteSettings,
    UserProfile,
    WhySection,
)
from .utils import calculate_totals, get_session_key, get_staff_unread_chat_counts


def customer_can_manage_order(request, order):
    if request.user.is_authenticated:
        return order.user_id == request.user.id
    return str(order.tracking_id) in get_guest_tracking_ids(request)


def get_guest_tracking_ids(request):
    tracking_ids = request.session.get("guest_tracking_ids", [])
    if not isinstance(tracking_ids, list):
        tracking_ids = []
    return tracking_ids


def get_trackable_orders(request):
    if request.user.is_authenticated:
        orders = list(Order.objects.filter(user=request.user).order_by("-created_at"))
    else:
        tracking_ids = get_guest_tracking_ids(request)
        orders = list(Order.objects.filter(tracking_id__in=tracking_ids).order_by("-created_at"))

    visible_orders = [order for order in orders if order.is_tracking_visible_to_customer()]
    return visible_orders


def _cart_count(cart):
    return sum(int(item.get("quantity", 0)) for item in cart.values())


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


@require_GET
def health_check(request):
    return JsonResponse({
        "status": "ok",
        "timestamp": timezone.now().isoformat(),
    })


def HomeView(request):
    hero = HeroImage.objects.first()
    category = Category.objects.all()
    deal = DailyDeal.objects.prefetch_related("sections__items").first()
    why = WhySection.objects.first()
    popular_section = PopularDealsSection.objects.prefetch_related("deals").first()
    our_special = OurSpecial.objects.first()

    cart = request.session.get("cart", {})
    cart_count = _cart_count(cart)

    # Feedback list
    feedbacks = Feedback.objects.all().order_by('-created_at')

    form = None

    if request.user.is_authenticated:

        if request.method == "POST":
            form = FeedbackForm(request.POST)

            if form.is_valid():
                Feedback.objects.create(
                    user=request.user,
                    message=form.cleaned_data["message"],
                    rating=form.cleaned_data["rating"],
                )
                return redirect('Home')  
        else:
            form = FeedbackForm()

    return render(request, "home.html", {
        "hero": hero,
        "category": category,
        "deal": deal,
        "why": why,
        "popular": popular_section,
        "our_special": our_special,
        "feedbacks": feedbacks,
        "form": form,

        "cart_count": cart_count,
    })


def AboutView(request):
    return redirect("Home")

def MenuView(request):
    categories = Category.objects.prefetch_related("items__variants")

    cart = request.session.get("cart", {})
    cart_count = _cart_count(cart)

    return render(request, "menu.html", {
        "categories": categories,
        "cart_count": cart_count
    })

# ADD TO CART (SESSION BASED)
@require_POST
def add_to_cart(request):
    variant_id = str(request.POST.get("variant_id", "")).strip()
    quantity_raw = request.POST.get("quantity", "1")

    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        return JsonResponse({"status": "error", "message": "Invalid quantity."}, status=400)

    if not variant_id:
        return JsonResponse({"status": "error", "message": "Variant is required."}, status=400)

    if quantity <= 0 or quantity > 99:
        return JsonResponse({"status": "error", "message": "Quantity must be between 1 and 99."}, status=400)

    variant = get_object_or_404(ItemVariant, id=variant_id)
    cart = request.session.get("cart", {})
    already_exists = False

    if variant_id in cart:
        cart[variant_id]["quantity"] += quantity
        already_exists = True
    else:
        cart[variant_id] = {
            "name": variant.item.name,
            "image": variant.item.image.url if variant.item.image else "",
            "size": variant.size,
            "price": float(variant.price),
            "quantity": quantity,
        }

    _save_cart(request, cart)

    return JsonResponse({
        "status": "exists" if already_exists else "success",
        "cart_count": _cart_count(cart),
    })


def CartView(request):
    cart = request.session.get("cart", {})

    last_order = None
    profile = None
    guest = None
    trackable_orders = []

    if request.user.is_authenticated:
        profile, _created = UserProfile.objects.get_or_create(user=request.user)
        trackable_orders = get_trackable_orders(request)
        last_order = trackable_orders[0] if trackable_orders else None
    else:
        guest = request.session.get("guest_info")
        trackable_orders = get_trackable_orders(request)
        visible_tracking_ids = [str(order.tracking_id) for order in trackable_orders]
        if visible_tracking_ids != get_guest_tracking_ids(request):
            request.session["guest_tracking_ids"] = visible_tracking_ids
            request.session.modified = True
        request.session["last_tracking_id"] = visible_tracking_ids[0] if visible_tracking_ids else ""
        if not visible_tracking_ids:
            request.session.pop("last_tracking_id", None)
        last_order = trackable_orders[0] if trackable_orders else None

    for key, item in cart.items():
        item["total_price"] = item["price"] * item["quantity"]

    totals = calculate_totals(cart, request.user)

    cart_count = _cart_count(cart)

    return render(request, "cart.html", {
        "cart": cart,
        "last_order": last_order,
        "trackable_orders": trackable_orders,
        "cart_count": cart_count,
        "profile": profile,
        "guest": guest,
        **totals
    })

@require_POST
def remove_cart_item(request, variant_id):
    cart = request.session.get("cart", {})

    if variant_id in cart:
        del cart[variant_id]

    _save_cart(request, cart)

    totals = calculate_totals(cart, request.user)

    cart_count = _cart_count(cart)

    return JsonResponse({
        "cart_count": cart_count,
        **totals
    })

@require_POST
def update_cart(request, variant_id, action):
    if action not in {"increase", "decrease"}:
        return JsonResponse({"status": "error", "message": "Invalid cart action."}, status=400)

    cart = request.session.get("cart", {})

    if variant_id in cart:
        if action == "increase":
            cart[variant_id]["quantity"] += 1
        elif action == "decrease" and cart[variant_id]["quantity"] > 1:
            cart[variant_id]["quantity"] -= 1

    _save_cart(request, cart)

    totals = calculate_totals(cart, request.user)

    item = cart.get(variant_id)
    item_total = 0

    if item:
        item_total = item["price"] * item["quantity"]

    cart_count = _cart_count(cart)

    return JsonResponse({
        "quantity": item["quantity"] if item else 0,
        "item_total": item_total,
        "cart_count": cart_count,
        **totals
    })


@require_GET
def cart_totals(request):
    cart = request.session.get("cart", {})
    totals = calculate_totals(cart, request.user)
    return JsonResponse(totals)

@require_POST
def add_daily_deal(request, id):

    deal = get_object_or_404(DailyDeal, id=id)

    cart = request.session.get("cart", {})

    key = f"daily_{deal.id}"

    if key in cart:
        return JsonResponse({
            "status": "exists",
            "message": "Already in cart",
            "cart_count": _cart_count(cart)
        })

    cart[key] = {
        "name": deal.title,
        "image": deal.image.url if deal.image else "",
        "size": "Deal",
        "price": float(deal.price),
        "quantity": 1,
    }

    _save_cart(request, cart)

    return JsonResponse({
        "status": "success",
        "message": "Added to cart",
        "cart_count": _cart_count(cart)
    })

@require_POST
def add_popular_deal(request, id):

    deal = get_object_or_404(PopularDeal, id=id)

    cart = request.session.get("cart", {})

    key = f"popular_{deal.id}"

    if key in cart:
        return JsonResponse({
            "status": "exists",
            "message": "Already in cart",
            "cart_count": _cart_count(cart)
        })

    cart[key] = {
        "name": deal.title,
        "image": deal.image.url if deal.image else "",
        "size": "Deal",
        "price": float(deal.price),
        "quantity": 1,
    }

    _save_cart(request, cart)

    return JsonResponse({
        "status": "success",
        "message": "Added to cart",
        "cart_count": _cart_count(cart)
    })

@require_POST
def add_special(request, id):

    special = get_object_or_404(OurSpecial, id=id)

    cart = request.session.get("cart", {})

    key = f"special_{special.id}"

    if key in cart:
        return JsonResponse({
            "status": "exists",
            "message": "Already in cart",
            "cart_count": _cart_count(cart)
        })

    cart[key] = {
        "name": "Our Special",
        "image": special.main_image.url if special.main_image else "",
        "size": "Special",
        "price": float(special.price),
        "quantity": 1,
    }

    _save_cart(request, cart)

    return JsonResponse({
        "status": "success",
        "message": "Added to cart",
        "cart_count": _cart_count(cart)
    })


def checkout(request):
    # Checkout is rendered as part of the cart page.
    return redirect("Cart")


@require_POST
def place_order(request):
    cart = request.session.get("cart", {})

    if not cart:
        return JsonResponse({
            "status": "error",
            "message": "Cart is empty"
        }, status=400)

    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    address = (request.POST.get("address") or "").strip()

    if request.user.is_authenticated:
        name = name or request.user.get_full_name() or request.user.username
        email = email or request.user.email

        profile, _created = UserProfile.objects.get_or_create(user=request.user)
        phone = phone or (profile.phone or "").strip()
        address = address or (profile.address or "").strip()

    if not name:
        return JsonResponse({
            "status": "error",
            "message": "Full name is required"
        }, status=400)

    if not phone:
        return JsonResponse({
            "status": "error",
            "message": "Phone number is required"
        }, status=400)

    if not address:
        return JsonResponse({
            "status": "error",
            "message": "Address is required"
        }, status=400)

    # ✅ USE UTILS
    totals = calculate_totals(cart, request.user)

    if "total" not in totals:
        return JsonResponse({
            "status": "error",
            "message": "Pricing configuration is unavailable. Please try again shortly.",
        }, status=503)

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        name=name,
        email=email,
        phone=phone,
        address=address,
        total=totals["total"]   # ✅ Correct final total
    )
    order.initialize_tracking()

    for item in cart.values():
        OrderItem.objects.create(
            order=order,
            name=item["name"],
            size=item["size"],
            price=item["price"],
            quantity=item["quantity"]
        )

    # Save user info
    if request.user.is_authenticated:
        profile, _created = UserProfile.objects.get_or_create(user=request.user)
        profile.phone = phone
        profile.address = address
        profile.save(update_fields=["phone", "address"])
    else:
        request.session["guest_info"] = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
        }
        guest_tracking_ids = get_guest_tracking_ids(request)
        tracking_id_value = str(order.tracking_id)
        guest_tracking_ids = [tracking_id for tracking_id in guest_tracking_ids if tracking_id != tracking_id_value]
        guest_tracking_ids.insert(0, tracking_id_value)
        request.session["guest_tracking_ids"] = guest_tracking_ids[:10]

    request.session["last_tracking_id"] = str(order.tracking_id)

    _save_cart(request, {})

    return JsonResponse({
        "status": "success",
        "tracking_id": str(order.tracking_id),
        "order_number": order.order_number,
        "order_status": order.status,
        "order_status_label": order.get_status_display(),
        "status_message": order.get_status_message(),
    })


def track_order(request, tracking_id):
    order = get_object_or_404(Order, tracking_id=tracking_id)
    if not request.user.is_staff and not customer_can_manage_order(request, order):
        return JsonResponse({
            "status": "error",
            "message": "You cannot view this order.",
        }, status=403)

    if not order.is_tracking_visible_to_customer():
        if not request.user.is_authenticated:
            tracking_id_value = str(order.tracking_id)
            guest_tracking_ids = [value for value in get_guest_tracking_ids(request) if value != tracking_id_value]
            request.session["guest_tracking_ids"] = guest_tracking_ids
            if str(request.session.get("last_tracking_id")) == tracking_id_value:
                request.session["last_tracking_id"] = guest_tracking_ids[0] if guest_tracking_ids else ""
                if not guest_tracking_ids:
                    request.session.pop("last_tracking_id", None)
            request.session.modified = True
        return JsonResponse({
            "status": "expired",
            "message": "This order is no longer available in customer tracking.",
        }, status=410)
    return JsonResponse({
        "status": "success",
        **order.get_tracking_data()
    })


@require_POST
def cancel_order(request, tracking_id):
    order = get_object_or_404(Order, tracking_id=tracking_id)

    if not customer_can_manage_order(request, order):
        return JsonResponse({"status": "error", "message": "You cannot cancel this order."}, status=403)

    if not order.can_customer_cancel():
        return JsonResponse({
            "status": "error",
            "message": "This order can only be cancelled within the first few minutes after placing it.",
        }, status=400)

    order.advance_status(
        new_status="cancelled",
        changed_by=request.user if request.user.is_authenticated else None,
        is_automatic=False,
        note="Order cancelled by customer from tracking popup.",
        customer_message="Your order has been cancelled successfully.",
    )

    return JsonResponse({
        "status": "success",
        "message": "Your order has been cancelled.",
        **order.get_tracking_data(),
    })


def _get_live_chat_settings():
    return SiteSettings.objects.first()


def _get_live_chat_display_name(request):
    if request.user.is_authenticated:
        full_name = request.user.get_full_name().strip()
        return full_name or request.user.username

    guest_info = request.session.get("guest_info", {}) or {}
    guest_name = str(guest_info.get("name", "")).strip()
    return guest_name or "Anonymous User"


def _get_or_create_live_chat_thread(request):
    session_key = get_session_key(request)
    display_name = _get_live_chat_display_name(request)

    if request.user.is_authenticated:
        thread = (
            LiveChatThread.objects
            .filter(user=request.user)
            .order_by("-last_message_at", "-updated_at")
            .first()
        )
        if thread:
            update_fields = []
            if thread.session_key != session_key:
                thread.session_key = session_key
                update_fields.append("session_key")
            if thread.display_name != display_name:
                thread.display_name = display_name
                update_fields.append("display_name")
            if not thread.is_authenticated_user:
                thread.is_authenticated_user = True
                update_fields.append("is_authenticated_user")
            if update_fields:
                thread.save(update_fields=update_fields + ["updated_at"])
            return thread

        return LiveChatThread.objects.create(
            user=request.user,
            session_key=session_key,
            display_name=display_name,
            is_authenticated_user=True,
            last_message_at=timezone.now(),
        )

    thread = (
        LiveChatThread.objects
        .filter(user__isnull=True, session_key=session_key)
        .order_by("-last_message_at", "-updated_at")
        .first()
    )
    if thread:
        update_fields = []
        if thread.display_name != display_name:
            thread.display_name = display_name
            update_fields.append("display_name")
        if thread.is_authenticated_user:
            thread.is_authenticated_user = False
            update_fields.append("is_authenticated_user")
        if update_fields:
            thread.save(update_fields=update_fields + ["updated_at"])
        return thread

    return LiveChatThread.objects.create(
        session_key=session_key,
        display_name=display_name,
        is_authenticated_user=False,
        last_message_at=timezone.now(),
    )


def _serialize_chat_message(message, customer_view=False):
    sender_label = message.get_sender_type_display()
    is_mine = message.sender_type == LiveChatMessage.SENDER_CUSTOMER
    if customer_view:
        if message.sender_type == LiveChatMessage.SENDER_CUSTOMER:
            sender_label = "You"
        elif message.sender_type == LiveChatMessage.SENDER_ADMIN:
            sender_label = "Support"
        else:
            sender_label = "Support Bot"

    return {
        "id": message.id,
        "sender_type": message.sender_type,
        "sender_label": sender_label,
        "is_mine": is_mine,
        "message_text": message.message_text,
        "created_at": message.created_at.isoformat(),
    }


def _touch_live_chat_thread(thread, timestamp=None):
    thread.last_message_at = timestamp or timezone.now()
    thread.save(update_fields=["last_message_at", "updated_at"])


def _get_admin_seen_map(request):
    seen_map = request.session.get("admin_live_chat_seen", {})
    if not isinstance(seen_map, dict):
        return {}
    return seen_map


def _save_admin_seen_map(request, seen_map):
    request.session["admin_live_chat_seen"] = seen_map
    request.session.modified = True


def _get_latest_customer_message_id(thread):
    latest_customer_id = (
        thread.messages
        .filter(sender_type=LiveChatMessage.SENDER_CUSTOMER)
        .order_by("-id")
        .values_list("id", flat=True)
        .first()
    )
    return int(latest_customer_id or 0)


def _mark_thread_as_seen_for_admin(request, thread):
    latest_customer_message_id = _get_latest_customer_message_id(thread)
    if latest_customer_message_id <= 0:
        return

    seen_map = _get_admin_seen_map(request)
    key = str(thread.id)
    previous_seen = 0
    try:
        previous_seen = int(seen_map.get(key, 0))
    except (TypeError, ValueError):
        previous_seen = 0

    if latest_customer_message_id > previous_seen:
        seen_map[key] = latest_customer_message_id
        _save_admin_seen_map(request, seen_map)


def _get_thread_unread_customer_count(thread, seen_map):
    seen_message_id = 0
    try:
        seen_message_id = int(seen_map.get(str(thread.id), 0))
    except (TypeError, ValueError):
        seen_message_id = 0

    latest_customer_message_id = _get_latest_customer_message_id(thread)
    if latest_customer_message_id <= seen_message_id:
        return 0

    return thread.messages.filter(
        sender_type=LiveChatMessage.SENDER_CUSTOMER,
        id__gt=seen_message_id,
    ).count()


def _extract_live_chat_message(request):
    content_type = request.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return ""
        return str(payload.get("message", "")).strip()

    return str(request.POST.get("message", "")).strip()


@require_GET
def live_chat_bootstrap(request):
    settings_obj = _get_live_chat_settings()
    chat_enabled = getattr(settings_obj, "chat_is_enabled", True)

    if not chat_enabled:
        return JsonResponse({"status": "success", "chat_enabled": False})

    thread = _get_or_create_live_chat_thread(request)

    messages = list(thread.messages.all().order_by("id")[:120])
    last_message_id = messages[-1].id if messages else 0

    return JsonResponse({
        "status": "success",
        "chat_enabled": True,
        "thread": {
            "id": thread.id,
            "display_name": thread.display_name,
            "is_authenticated_user": thread.is_authenticated_user,
            "is_closed": thread.is_closed,
        },
        "messages": [_serialize_chat_message(message, customer_view=True) for message in messages],
        "last_message_id": last_message_id,
    })


@require_GET
def live_chat_messages(request):
    settings_obj = _get_live_chat_settings()
    chat_enabled = getattr(settings_obj, "chat_is_enabled", True)

    if not chat_enabled:
        return JsonResponse({"status": "success", "chat_enabled": False, "messages": [], "last_message_id": 0})

    thread = _get_or_create_live_chat_thread(request)
    since_id = request.GET.get("since_id", "0")
    try:
        since_id = int(since_id)
    except (TypeError, ValueError):
        since_id = 0

    message_queryset = thread.messages.all().order_by("id")
    if since_id > 0:
        message_queryset = message_queryset.filter(id__gt=since_id)

    messages = list(message_queryset[:120])
    last_message_id = since_id
    if messages:
        last_message_id = messages[-1].id

    return JsonResponse({
        "status": "success",
        "chat_enabled": True,
        "thread_id": thread.id,
        "messages": [_serialize_chat_message(message, customer_view=True) for message in messages],
        "last_message_id": last_message_id,
    })


@require_POST
def live_chat_send(request):
    settings_obj = _get_live_chat_settings()
    chat_enabled = getattr(settings_obj, "chat_is_enabled", True)
    if not chat_enabled:
        return JsonResponse({"status": "error", "message": "Live chat is currently unavailable."}, status=403)

    message_text = _extract_live_chat_message(request)
    if not message_text:
        return JsonResponse({"status": "error", "message": "Please type a message."}, status=400)

    if len(message_text) > 1200:
        return JsonResponse({"status": "error", "message": "Message is too long."}, status=400)

    thread = _get_or_create_live_chat_thread(request)
    had_customer_message = thread.messages.filter(sender_type=LiveChatMessage.SENDER_CUSTOMER).exists()

    message = LiveChatMessage.objects.create(
        thread=thread,
        sender_type=LiveChatMessage.SENDER_CUSTOMER,
        message_text=message_text,
    )
    created_messages = [message]

    auto_response = ""
    if settings_obj:
        auto_response = (settings_obj.chat_auto_response or "").strip()

    should_send_auto = (
        not had_customer_message
        and bool(auto_response)
        and not thread.messages.exclude(pk=message.pk).filter(sender_type=LiveChatMessage.SENDER_SYSTEM).exists()
    )

    if should_send_auto:
        auto_message = LiveChatMessage.objects.create(
            thread=thread,
            sender_type=LiveChatMessage.SENDER_SYSTEM,
            message_text=auto_response,
        )
        created_messages.append(auto_message)

    _touch_live_chat_thread(thread, created_messages[-1].created_at)
    customer_messages = [_serialize_chat_message(item, customer_view=True) for item in created_messages]

    return JsonResponse({
        "status": "success",
        "thread_id": thread.id,
        "message": customer_messages[0],
        "messages": customer_messages,
        "last_message_id": customer_messages[-1]["id"],
    })


@staff_member_required
def live_chat_dashboard(request):
    return render(request, "admin/live_chat_dashboard.html")


@staff_member_required
@require_GET
def staff_live_chat_threads(request):
    query = str(request.GET.get("q", "")).strip()
    seen_map = _get_admin_seen_map(request)
    thread_queryset = LiveChatThread.objects.select_related("user").all()

    if query:
        thread_queryset = thread_queryset.filter(
            Q(display_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__email__icontains=query)
            | Q(session_key__icontains=query)
        )

    thread_queryset = thread_queryset.order_by("-last_message_at", "-updated_at")[:150]
    thread_rows = []

    for thread in thread_queryset:
        last_message = thread.messages.order_by("-id").first()
        unread_count = _get_thread_unread_customer_count(thread, seen_map)

        thread_rows.append({
            "id": thread.id,
            "display_name": thread.display_name,
            "is_authenticated_user": thread.is_authenticated_user,
            "is_closed": thread.is_closed,
            "unread_count": unread_count,
            "last_message_text": last_message.message_text if last_message else "",
            "last_message_sender": last_message.get_sender_type_display() if last_message else "",
            "last_message_at": thread.last_message_at.isoformat() if thread.last_message_at else "",
        })

    return JsonResponse({"status": "success", "threads": thread_rows})


@staff_member_required
@require_GET
def staff_live_chat_unread_count(request):
    unread_counts = get_staff_unread_chat_counts(seen_map=_get_admin_seen_map(request))
    return JsonResponse({
        "status": "success",
        "unread_threads": unread_counts["threads"],
        "unread_messages": unread_counts["messages"],
    })


@staff_member_required
@require_GET
def staff_live_chat_messages(request, thread_id):
    thread = get_object_or_404(LiveChatThread, pk=thread_id)
    since_id = request.GET.get("since_id", "0")
    try:
        since_id = int(since_id)
    except (TypeError, ValueError):
        since_id = 0

    message_queryset = thread.messages.order_by("id")
    if since_id > 0:
        message_queryset = message_queryset.filter(id__gt=since_id)

    messages = list(message_queryset[:200])
    last_message_id = since_id
    if messages:
        last_message_id = messages[-1].id

    _mark_thread_as_seen_for_admin(request, thread)

    return JsonResponse({
        "status": "success",
        "thread": {
            "id": thread.id,
            "display_name": thread.display_name,
            "is_authenticated_user": thread.is_authenticated_user,
            "is_closed": thread.is_closed,
        },
        "messages": [_serialize_chat_message(message, customer_view=False) for message in messages],
        "last_message_id": last_message_id,
    })


@staff_member_required
@require_POST
def staff_live_chat_send(request, thread_id):
    thread = get_object_or_404(LiveChatThread, pk=thread_id)
    message_text = _extract_live_chat_message(request)
    if not message_text:
        return JsonResponse({"status": "error", "message": "Please type a message."}, status=400)

    if len(message_text) > 1200:
        return JsonResponse({"status": "error", "message": "Message is too long."}, status=400)

    message = LiveChatMessage.objects.create(
        thread=thread,
        sender_type=LiveChatMessage.SENDER_ADMIN,
        message_text=message_text,
    )
    _touch_live_chat_thread(thread, message.created_at)
    _mark_thread_as_seen_for_admin(request, thread)

    return JsonResponse({
        "status": "success",
        "message": _serialize_chat_message(message, customer_view=False),
        "last_message_id": message.id,
    })
