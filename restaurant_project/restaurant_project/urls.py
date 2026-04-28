from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from food.views import (
    CartView,
    HomeView,
    MenuView,
    add_daily_deal,
    add_popular_deal,
    add_special,
    add_to_cart,
    cancel_order,
    cart_totals,
    checkout,
    health_check,
    live_chat_bootstrap,
    live_chat_dashboard,
    live_chat_messages,
    live_chat_send,
    place_order,
    remove_cart_item,
    staff_live_chat_messages,
    staff_live_chat_send,
    staff_live_chat_threads,
    staff_live_chat_unread_count,
    track_order,
    update_cart,
)


urlpatterns = [
    path("admin/live-chat/", live_chat_dashboard, name="live_chat_dashboard"),
    path("admin/live-chat/threads/", staff_live_chat_threads, name="staff_live_chat_threads"),
    path("admin/live-chat/unread-count/", staff_live_chat_unread_count, name="staff_live_chat_unread_count"),
    path("admin/live-chat/threads/<int:thread_id>/messages/", staff_live_chat_messages, name="staff_live_chat_messages"),
    path("admin/live-chat/threads/<int:thread_id>/send/", staff_live_chat_send, name="staff_live_chat_send"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", HomeView, name="Home"),
    path("menu/", MenuView, name="Menu"),
    path("menu", MenuView),
    path("add-to-cart/", add_to_cart, name="add_to_cart"),
    path("cart/", CartView, name="Cart"),
    path("cart/remove/<str:variant_id>/", remove_cart_item, name="remove_cart_item"),
    path("cart/update/<str:variant_id>/<str:action>/", update_cart, name="update_cart"),
    path("cart/totals/", cart_totals, name="cart_totals"),
    path("cart/add-daily-deal/<int:id>/", add_daily_deal, name="add_daily_deal"),
    path("cart/add-popular-deal/<int:id>/", add_popular_deal, name="add_popular_deal"),
    path("cart/add-special/<int:id>/", add_special, name="add_special"),
    path("checkout/", checkout, name="checkout"),
    path("health/", health_check, name="health_check"),
    path("place-order/", place_order, name="place_order"),
    path("track-order/<uuid:tracking_id>/", track_order, name="track_order"),
    path("cancel-order/<uuid:tracking_id>/", cancel_order, name="cancel_order"),
    path("live-chat/bootstrap/", live_chat_bootstrap, name="live_chat_bootstrap"),
    path("live-chat/messages/", live_chat_messages, name="live_chat_messages"),
    path("live-chat/send/", live_chat_send, name="live_chat_send"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
