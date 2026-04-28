import json
from datetime import timedelta
from decimal import Decimal

from django.contrib import admin
from django.db.models import Sum
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from food.models import *

# Register your models here.

admin.site.site_header = "Little Lemon Control Room"
admin.site.site_title = "Little Lemon Admin"
admin.site.index_title = "Content, pricing, and order operations"

admin.site.register(HeroImage)

admin.site.register(Category)

class ItemVariantInline(admin.TabularInline):
    model = ItemVariant
    extra = 1
    max_num = 4

class ItemAdmin(admin.ModelAdmin):
    inlines = [ItemVariantInline]

admin.site.register(Item, ItemAdmin)

# for the Day of Deal Section 

class DealItemInline(admin.TabularInline):
    model = DealItem
    extra = 1


class DealSectionInline(admin.TabularInline):
    model = DealSection
    extra = 1
    show_change_link = True


@admin.register(DailyDeal)
class DayDealAdmin(admin.ModelAdmin):
    list_display = ("title", "price")
    inlines = [DealSectionInline]

    class Meta:
        verbose_name = "Day Deal"
        verbose_name_plural = "Day Deals"


# Hide sections and items from sidebar
@admin.register(DealSection)
class DealSectionAdmin(admin.ModelAdmin):
    list_display = ("heading", "deal", "order")
    inlines = [DealItemInline]

    def has_module_permission(self, request):
        return False


@admin.register(DealItem)
class DealItemAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False


# Why Section //


class WhyFeatureInline(admin.TabularInline):
    model = WhyFeature
    extra = 0
    max_num = 3


@admin.register(WhySection)
class WhySectionAdmin(admin.ModelAdmin):
    inlines = [WhyFeatureInline]


# Popular Deals Section 


class PopularDealInline(admin.TabularInline):
    model = PopularDeal
    extra = 1


@admin.register(PopularDealsSection)
class PopularDealsSectionAdmin(admin.ModelAdmin):
    inlines = [PopularDealInline]

    # prevent adding more than one section
    def has_add_permission(self, request):
        if PopularDealsSection.objects.exists():
            return False
        return True
    

# Our Special //

from django.contrib import admin
from .models import OurSpecial, OurSpecialCard


class OurSpecialCardInline(admin.TabularInline):
    model = OurSpecialCard
    extra = 0
    max_num = 3      # HARD LIMIT
    can_delete = True


@admin.register(OurSpecial)
class OurSpecialAdmin(admin.ModelAdmin):
    inlines = [OurSpecialCardInline]

    def has_add_permission(self, request):
        # Prevent adding more than ONE section
        return not OurSpecial.objects.exists()



# For Admin Discounts and Tax 

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):

    list_display = (
        "active_theme",
        "chat_is_enabled",
        "tax_percent",
        "delivery_fee",
        "customer_cancel_window_minutes",
        "tracking_visibility_after_delivery_minutes",
        "tracking_visibility_after_cancellation_minutes",
        "global_discount_percent",
        "auth_user_discount_percent",
        "special_discount_percent",
        "special_discount_start",
        "special_discount_end",
    )

    # ❌ Remove "Add" button if already exists
    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return True
    fieldsets = (
        ("Brand Theme", {
            "fields": ("active_theme",),
        }),
        ("Live Chat", {
            "description": "Control customer live chat visibility and first automatic response.",
            "fields": ("chat_is_enabled", "chat_auto_response"),
        }),
        ("Tax & Delivery", {
            "fields": (
                "tax_percent",
                "delivery_fee",
                "free_delivery_threshold",   # 👈 ADD THIS
            ),
        }),
        ("Regular Discount", {
            "fields": ("global_discount_percent",),
        }),
        ("User Discount", {
            "fields": ("auth_user_discount_percent",),
        }),
        ("Special Limited Offer", {
            "fields": (
                "special_discount_percent",
                "special_discount_start",
                "special_discount_end",
            ),
        }),
        ("Customer Order Controls", {
            "description": "Control how long customers can cancel and how long delivered/cancelled orders remain visible in tracking.",
            "fields": (
                "customer_cancel_window_minutes",
                "tracking_visibility_after_delivery_minutes",
                "tracking_visibility_after_cancellation_minutes",
            ),
        }),
    )
    
class OrderItemInline(admin.TabularInline):

    model = OrderItem
    extra = 0


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False
    fields = (
        "changed_at",
        "status",
        "previous_status",
        "is_automatic",
        "changed_by",
        "note",
        "customer_message",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(OrderStatusAutomationRule)
class OrderStatusAutomationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "from_status",
        "to_status",
        "delay_minutes",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active", "from_status", "to_status")
    search_fields = ("customer_message", "admin_note")
    fieldsets = (
        ("Automation Flow", {
            "description": "Configure automatic status changes for active orders. Disable a rule any time to stop that auto-step.",
            "fields": ("from_status", "to_status", "delay_minutes", "is_active"),
        }),
        ("Customer Communication", {
            "description": "These messages appear in the customer tracking popup when the auto-update happens.",
            "fields": ("customer_message", "admin_note"),
        }),
    )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "status",
        "previous_status",
        "is_automatic",
        "changed_by",
        "changed_at",
    )
    list_filter = ("status", "is_automatic", "changed_at")
    search_fields = ("order__tracking_id__exact", "order__name", "note", "customer_message")
    readonly_fields = (
        "order",
        "status",
        "previous_status",
        "is_automatic",
        "changed_by",
        "note",
        "customer_message",
        "changed_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/food/order/change_list.html"

    list_display = (

        "id",
        "order_number",
        "tracking_id",
        "name",
        "phone",
        "total",
        "status_control",
        "status_updated_at",
        "next_auto_status_at",
        "created_at",
    )

    list_filter = ("status", "status_updated_at", "created_at")
    readonly_fields = (
        "order_number",
        "tracking_id",
        "created_at",
        "status_updated_at",
        "next_auto_status_at",
        "delivered_at",
        "cancelled_at",
    )
    search_fields = ("order_number__exact", "tracking_id__exact", "name", "phone", "email")
    date_hierarchy = "created_at"
    list_per_page = 25
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    fieldsets = (
        ("Customer", {
            "description": "Customer contact details captured from checkout.",
            "fields": ("user", "name", "email", "phone", "address"),
        }),
        ("Order", {
            "description": "Use the daily order number for phone support and quick employee search.",
            "fields": ("order_number", "tracking_id", "total", "status"),
        }),
        ("Tracking", {
            "description": "These fields update automatically when the status changes manually or through automation rules.",
            "fields": ("status_updated_at", "next_auto_status_at", "delivered_at", "cancelled_at", "created_at"),
        }),
    )

    class Media:
        js = ("admin/order_admin.js",)
        css = {
            "all": ("admin/order_admin.css",)
        }

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        order_queryset = Order.objects.all()
        status_counts = {
            value: order_queryset.filter(status=value).count()
            for value, _label in Order.STATUS_CHOICES
        }
        total_orders = order_queryset.count()
        current_status = request.GET.get("status__exact", "")
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=6)

        def revenue_for(queryset):
            return queryset.aggregate(total=Sum("total")).get("total") or Decimal("0.00")

        today_orders = order_queryset.filter(created_at__date=today)
        yesterday_orders = order_queryset.filter(created_at__date=yesterday)
        week_orders = order_queryset.filter(created_at__date__gte=start_of_week)

        daily_rows = []
        for offset in range(6, -1, -1):
            target_day = today - timedelta(days=offset)
            day_queryset = order_queryset.filter(created_at__date=target_day)
            daily_rows.append({
                "date_label": target_day.strftime("%b %d, %Y"),
                "orders": day_queryset.count(),
                "revenue": revenue_for(day_queryset),
                "delivered": day_queryset.filter(status="delivered").count(),
                "cancelled": day_queryset.filter(status="cancelled").count(),
            })

        extra_context["order_status_tabs"] = [
            {
                "label": "All",
                "count": total_orders,
                "url": ".",
                "active": current_status == "",
                "css_class": "status-all",
            },
            *[
                {
                    "label": label,
                    "count": status_counts.get(value, 0),
                    "url": f"?status__exact={value}",
                    "active": current_status == value,
                    "css_class": f"status-{value}",
                }
                for value, label in Order.STATUS_CHOICES
            ],
        ]
        extra_context["order_kpis"] = [
            {
                "label": "Today's Orders",
                "value": today_orders.count(),
                "accent": "accent-amber",
                "help_text": "New orders placed today.",
            },
            {
                "label": "Today's Revenue",
                "value": f"Rs. {revenue_for(today_orders):,.2f}",
                "accent": "accent-green",
                "help_text": "Total order value created today.",
            },
            {
                "label": "Delivered Today",
                "value": today_orders.filter(status='delivered').count(),
                "accent": "accent-blue",
                "help_text": "Orders completed today.",
            },
            {
                "label": "Open Kitchen Queue",
                "value": order_queryset.filter(status__in=["pending", "confirmed", "preparing", "out_for_delivery"]).count(),
                "accent": "accent-orange",
                "help_text": "Orders still in progress right now.",
            },
            {
                "label": "Yesterday Revenue",
                "value": f"Rs. {revenue_for(yesterday_orders):,.2f}",
                "accent": "accent-slate",
                "help_text": "Previous day revenue for quick comparison.",
            },
            {
                "label": "7-Day Revenue",
                "value": f"Rs. {revenue_for(week_orders):,.2f}",
                "accent": "accent-purple",
                "help_text": "Rolling revenue across the last 7 days.",
            },
        ]
        extra_context["daily_order_rows"] = daily_rows

        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/quick-status/",
                self.admin_site.admin_view(self.quick_status_view),
                name="food_order_quick_status",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Status")
    def status_control(self, obj):
        options_html = "".join(
            f'<option value="{value}"{" selected" if value == obj.status else ""}>{label}</option>'
            for value, label in Order.STATUS_CHOICES
        )
        return format_html(
            '<div class="status-control status-{}" data-order-id="{}">'
            '<div class="status-control-row">'
            '<select class="quick-status-select" data-status-url="{}" aria-label="Update order status">{}</select>'
            '<button type="button" class="quick-status-button" onclick="window.quickOrderStatusUpdate && window.quickOrderStatusUpdate(this)">Update</button>'
            '<a href="{}" class="quick-status-open">Open</a>'
            "</div>"
            '<span class="status-update-feedback" aria-live="polite"></span>'
            "</div>",
            obj.status,
            obj.pk,
            reverse("admin:food_order_quick_status", args=[obj.pk]),
            mark_safe(options_html),
            reverse("admin:food_order_change", args=[obj.pk]),
        )

    def quick_status_view(self, request, object_id):
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

        order = self.get_object(request, object_id)
        if not order:
            return JsonResponse({"status": "error", "message": "Order not found."}, status=404)

        if not self.has_change_permission(request, order):
            return JsonResponse({"status": "error", "message": "Permission denied."}, status=403)

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid payload."}, status=400)

        new_status = payload.get("status")
        valid_statuses = {value for value, _label in Order.STATUS_CHOICES}
        if new_status not in valid_statuses:
            return JsonResponse({"status": "error", "message": "Invalid order status."}, status=400)

        if new_status == order.status:
            order.ensure_tracking_state(save=True)
            return JsonResponse({
                "status": "success",
                "order_status": order.status,
                "order_status_label": order.get_status_display(),
                "updated_at": timezone.localtime(order.status_updated_at or timezone.now()).strftime("%b %d, %Y %I:%M %p"),
                "message": "No change needed.",
            })

        order.advance_status(
            new_status=new_status,
            changed_by=request.user,
            is_automatic=False,
            note="Status updated from the order list.",
            customer_message=f"Your order is now {dict(Order.STATUS_CHOICES).get(new_status, new_status)}.",
        )
        order.refresh_from_db()

        return JsonResponse({
            "status": "success",
            "order_status": order.status,
            "order_status_label": order.get_status_display(),
            "updated_at": timezone.localtime(order.status_updated_at).strftime("%b %d, %Y %I:%M %p"),
            "message": "Status updated.",
        })

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = Order.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        if not change:
            obj.initialize_tracking()
            return

        if previous_status != obj.status:
            changed_at = timezone.now()
            obj.status_updated_at = changed_at
            obj.delivered_at = changed_at if obj.status == "delivered" else None
            obj.cancelled_at = changed_at if obj.status == "cancelled" else None
            obj.next_auto_status_at = obj.calculate_next_auto_status_at(changed_at)

            Order.objects.filter(pk=obj.pk).update(
                status_updated_at=obj.status_updated_at,
                delivered_at=obj.delivered_at,
                cancelled_at=obj.cancelled_at,
                next_auto_status_at=obj.next_auto_status_at,
            )

            OrderStatusHistory.objects.create(
                order=obj,
                previous_status=previous_status or "",
                status=obj.status,
                changed_by=request.user,
                is_automatic=False,
                note="Status updated manually by admin.",
                customer_message=f"Your order is now {obj.get_status_display()}.",
                changed_at=changed_at,
            )


class LiveChatMessageInline(admin.TabularInline):
    model = LiveChatMessage
    extra = 0
    fields = ("sender_type", "message_text", "created_at")
    readonly_fields = ("created_at",)


@admin.register(LiveChatThread)
class LiveChatThreadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "display_name",
        "is_authenticated_user",
        "user",
        "is_closed",
        "last_message_at",
        "created_at",
    )
    list_filter = ("is_authenticated_user", "is_closed", "last_message_at")
    search_fields = ("display_name", "user__username", "user__email", "session_key")
    readonly_fields = ("session_key", "created_at", "updated_at", "last_message_at")
    inlines = [LiveChatMessageInline]


@admin.register(LiveChatMessage)
class LiveChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "sender_type", "short_message", "created_at")
    list_filter = ("sender_type", "created_at")
    search_fields = ("thread__display_name", "thread__user__username", "message_text")
    readonly_fields = ("thread", "sender_type", "message_text", "created_at")

    def has_add_permission(self, request):
        return False

    @admin.display(description="Message")
    def short_message(self, obj):
        message = obj.message_text or ""
        return message if len(message) <= 90 else f"{message[:87]}..."

