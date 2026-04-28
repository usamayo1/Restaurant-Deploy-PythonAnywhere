from .models import SiteSettings
from .utils import get_staff_unread_chat_counts


def active_theme(request):
    settings_obj = SiteSettings.objects.only("active_theme").first()
    return {
        "active_theme": getattr(settings_obj, "active_theme", "default") or "default",
    }


def admin_live_chat_counts(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return {
            "admin_live_chat_unread_threads": 0,
            "admin_live_chat_unread_messages": 0,
        }
    if not request.path.startswith("/admin/"):
        return {
            "admin_live_chat_unread_threads": 0,
            "admin_live_chat_unread_messages": 0,
        }

    seen_map = request.session.get("admin_live_chat_seen", {})
    if not isinstance(seen_map, dict):
        seen_map = {}
    unread_counts = get_staff_unread_chat_counts(seen_map=seen_map)
    return {
        "admin_live_chat_unread_threads": unread_counts["threads"],
        "admin_live_chat_unread_messages": unread_counts["messages"],
    }
