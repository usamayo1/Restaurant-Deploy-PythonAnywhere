import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# Create your models here.

class HeroImage(models.Model):
    image1 = models.ImageField(upload_to='home/')
    image2 = models.ImageField(upload_to='home/')

class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=300, null=True, blank=True)
    image = models.ImageField(upload_to='home/', null=True, blank=True)
    
    def __str__(self):
        return self.name
    
class Item(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to="items/", null=True, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items"
    )

    def __str__(self):
        return self.name
    
class ItemVariant(models.Model):

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="variants")

    size = models.CharField(max_length=50)   # ✅ no choices, admin can type anything

    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.item.name} - {self.size}"
    

# For the Day of Deal 


class DailyDeal(models.Model):
    title = models.CharField(max_length=100, default="Deal of the Day")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="deals/", blank=True, null=True)

    def __str__(self):
        return self.title


class DealSection(models.Model):
    deal = models.ForeignKey(DailyDeal, on_delete=models.CASCADE, related_name="sections")
    heading = models.CharField(max_length=100)   # e.g. "Spring Rolls", "Fries"
    order = models.PositiveIntegerField(default=0)  # to control position

    def __str__(self):
        return f"{self.deal} - {self.heading}"


class DealItem(models.Model):
    section = models.ForeignKey(DealSection, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=200)   # e.g. "2 Tikka Rolls"

    def __str__(self):
        return self.name
    

# Why Section Models //



class WhySection(models.Model):
    title = models.CharField(max_length=200, default="Why People Choose Us?")
    main_image = models.ImageField(upload_to="why_section/", null=True, blank=True)

    def clean(self):
        # Prevent more than one WhySection
        if WhySection.objects.exclude(id=self.id).exists():
            raise ValidationError("Only one Why Section is allowed. You can add 3 Why features")

    def __str__(self):
        return "Why Section"


class WhyFeature(models.Model):
    section = models.ForeignKey(
        WhySection,
        on_delete=models.CASCADE,
        related_name="features"
    )
    image = models.ImageField(upload_to="why_section/features/")
    heading = models.CharField(max_length=150)
    description = models.CharField(max_length=300, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.heading



# Popular Deals Section //



class PopularDealsSection(models.Model):
    title = models.CharField(
        max_length=100,
        default="Popular Deals"
    )

    def clean(self):
        # Allow only one Popular Deals section
        if PopularDealsSection.objects.exclude(id=self.id).exists():
            from django.core.exceptions import ValidationError
            raise ValidationError("Only one Popular Deals section is allowed.")

    def __str__(self):
        return "Popular Deals Section"


class PopularDeal(models.Model):
    section = models.ForeignKey(
        PopularDealsSection,
        on_delete=models.CASCADE,
        related_name="deals"
    )
    image = models.ImageField(upload_to="popular_deals/")
    title = models.CharField(
        max_length=80,   # one line only
        help_text="Short title (one line)"
    )
    description = models.CharField(
        max_length=180,  # 2–3 lines max
        help_text="Short description (2–3 lines max)"
    )
    price = models.DecimalField(max_digits=8, decimal_places=2)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title
    

# OUR SPECIAL //



class OurSpecial(models.Model):
    main_image = models.ImageField(upload_to="our_special/")
    description = models.CharField(max_length=220)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return "Our Special Section"


class OurSpecialCard(models.Model):
    section = models.ForeignKey(
        OurSpecial,
        related_name="cards",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=40)
    description = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

# For the Add to cart system for deals of Home Page anad even for Menu item
class CartItem(models.Model):

    session_key = models.CharField(max_length=40)

    item_variant = models.ForeignKey(
        ItemVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    daily_deal = models.ForeignKey(
        DailyDeal,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    popular_deal = models.ForeignKey(
        PopularDeal,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    our_special = models.ForeignKey(
        OurSpecial,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.session_key}"

# For Google profile 

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    marketing_opt_in = models.BooleanField(default=True)

    profile_image = models.URLField(blank=True, null=True)  # ADD THIS

    def __str__(self):
        return self.user.username


# For FeedBack Model 

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feedbacks")
    message = models.TextField()
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.rating}"

ORDER_STATUS_CHOICES = (
    ("pending", "Pending"),
    ("confirmed", "Confirmed"),
    ("preparing", "Preparing"),
    ("out_for_delivery", "Out for delivery"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
)

TERMINAL_ORDER_STATUSES = {"delivered", "cancelled"}


class OrderStatusAutomationRule(models.Model):
    from_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, unique=True)
    to_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES)
    delay_minutes = models.PositiveIntegerField(
        default=10,
        help_text="Automatically move to the next status after this many minutes.",
    )
    is_active = models.BooleanField(default=True)
    customer_message = models.CharField(max_length=220, blank=True)
    admin_note = models.CharField(max_length=220, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order Status Automation Rule"
        verbose_name_plural = "Order Status Automation Rules"

    def clean(self):
        if self.from_status == self.to_status:
            raise ValidationError("From status and to status cannot be the same.")
        if self.from_status in TERMINAL_ORDER_STATUSES:
            raise ValidationError("Delivered and cancelled orders cannot auto-progress.")

    def __str__(self):
        return f"{self.get_from_status_display()} -> {self.get_to_status_display()} ({self.delay_minutes} min)"

    @classmethod
    def for_status(cls, status):
        return cls.objects.filter(from_status=status, is_active=True).first()


class Order(models.Model):

    STATUS_CHOICES = ORDER_STATUS_CHOICES

    order_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )

    tracking_id = models.UUIDField(
        unique=True,
        editable=False,
        null=True,
        blank=True,
        db_index=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()

    total = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    status_updated_at = models.DateTimeField(null=True, blank=True)
    next_auto_status_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


    # ✅ AUTO GENERATE TRACKING ID
    def generate_order_number(self):
        date_code = timezone.localtime(timezone.now()).strftime("%Y%m%d")
        sequence = 1

        while True:
            order_number = f"ORD-{date_code}-{sequence:03d}"
            if not type(self).objects.filter(order_number=order_number).exists():
                return order_number
            sequence += 1

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if not self.tracking_id:
            self.tracking_id = uuid.uuid4()
        super().save(*args, **kwargs)

    def get_status_message(self):
        latest_history = self.status_history.order_by("-changed_at").first()
        if latest_history and latest_history.customer_message:
            return latest_history.customer_message

        default_messages = {
            "pending": "Your order has been received and is waiting for confirmation.",
            "confirmed": "Your order is confirmed and queued in the kitchen.",
            "preparing": "Our kitchen is preparing your food right now.",
            "out_for_delivery": "Your order is out for delivery.",
            "delivered": "Your order has been delivered. Enjoy your meal.",
            "cancelled": "This order has been cancelled.",
        }
        return default_messages.get(self.status, "Your order is being processed.")

    def get_delivered_message(self):
        if self.status == "delivered":
            return "Delivered successfully. Thank you for ordering with us."
        return ""

    def get_site_settings(self):
        return SiteSettings.objects.first()

    def get_customer_cancel_deadline(self):
        settings_obj = self.get_site_settings()
        cancel_window_minutes = getattr(settings_obj, "customer_cancel_window_minutes", 2)
        base_time = self.created_at or timezone.now()
        return base_time + timedelta(minutes=cancel_window_minutes)

    def can_customer_cancel(self):
        if self.status != "pending":
            return False
        return timezone.now() <= self.get_customer_cancel_deadline()

    def get_tracking_visibility_deadline(self):
        settings_obj = self.get_site_settings()

        if self.status == "delivered" and self.delivered_at:
            tracking_window_minutes = getattr(settings_obj, "tracking_visibility_after_delivery_minutes", 5)
            return self.delivered_at + timedelta(minutes=tracking_window_minutes)

        if self.status == "cancelled" and self.cancelled_at:
            tracking_window_minutes = getattr(
                settings_obj,
                "tracking_visibility_after_cancellation_minutes",
                5,
            )
            return self.cancelled_at + timedelta(minutes=tracking_window_minutes)

        return None

    def is_tracking_visible_to_customer(self):
        if self.status not in {"delivered", "cancelled"}:
            return True

        visibility_deadline = self.get_tracking_visibility_deadline()
        if not visibility_deadline:
            return True
        return timezone.now() <= visibility_deadline

    def get_active_automation_rule(self):
        return OrderStatusAutomationRule.for_status(self.status)

    def calculate_next_auto_status_at(self, base_time=None):
        if self.status in TERMINAL_ORDER_STATUSES:
            return None

        rule = self.get_active_automation_rule()
        if not rule:
            return None

        base_time = base_time or self.status_updated_at or self.created_at or timezone.now()
        return base_time + timedelta(minutes=rule.delay_minutes)

    def ensure_tracking_state(self, save=True):
        updates = {}
        base_time = self.status_updated_at or self.created_at or timezone.now()

        if self.status_updated_at is None:
            updates["status_updated_at"] = base_time

        expected_delivered_at = base_time if self.status == "delivered" else None
        if self.delivered_at != expected_delivered_at:
            updates["delivered_at"] = expected_delivered_at

        expected_cancelled_at = base_time if self.status == "cancelled" else None
        if self.cancelled_at != expected_cancelled_at:
            updates["cancelled_at"] = expected_cancelled_at

        expected_next_auto = self.calculate_next_auto_status_at(base_time)
        if self.next_auto_status_at != expected_next_auto:
            updates["next_auto_status_at"] = expected_next_auto

        if updates:
            for field, value in updates.items():
                setattr(self, field, value)

            if save and self.pk:
                type(self).objects.filter(pk=self.pk).update(**updates)

        return updates

    def add_status_history(
        self,
        previous_status="",
        changed_by=None,
        is_automatic=False,
        note="",
        customer_message="",
        changed_at=None,
    ):
        return OrderStatusHistory.objects.create(
            order=self,
            previous_status=previous_status,
            status=self.status,
            changed_by=changed_by,
            is_automatic=is_automatic,
            note=note,
            customer_message=customer_message or self.get_status_message(),
            changed_at=changed_at or timezone.now(),
        )

    def initialize_tracking(self):
        changed_at = self.created_at or timezone.now()
        self.status_updated_at = changed_at
        self.next_auto_status_at = self.calculate_next_auto_status_at(changed_at)
        self.delivered_at = changed_at if self.status == "delivered" else None
        self.cancelled_at = changed_at if self.status == "cancelled" else None

        type(self).objects.filter(pk=self.pk).update(
            status_updated_at=self.status_updated_at,
            next_auto_status_at=self.next_auto_status_at,
            delivered_at=self.delivered_at,
            cancelled_at=self.cancelled_at,
        )

        if not self.status_history.exists():
            self.add_status_history(
                previous_status="",
                note="Order placed successfully.",
                customer_message=self.get_status_message(),
                changed_at=changed_at,
            )

    def advance_status(
        self,
        new_status,
        changed_by=None,
        is_automatic=False,
        note="",
        customer_message="",
        changed_at=None,
    ):
        if new_status == self.status:
            self.ensure_tracking_state(save=True)
            return

        previous_status = self.status
        changed_at = changed_at or timezone.now()

        self.status = new_status
        self.status_updated_at = changed_at
        self.delivered_at = changed_at if new_status == "delivered" else None
        self.cancelled_at = changed_at if new_status == "cancelled" else None
        self.next_auto_status_at = self.calculate_next_auto_status_at(changed_at)

        type(self).objects.filter(pk=self.pk).update(
            status=self.status,
            status_updated_at=self.status_updated_at,
            delivered_at=self.delivered_at,
            cancelled_at=self.cancelled_at,
            next_auto_status_at=self.next_auto_status_at,
        )

        self.add_status_history(
            previous_status=previous_status,
            changed_by=changed_by,
            is_automatic=is_automatic,
            note=note,
            customer_message=customer_message,
            changed_at=changed_at,
        )

    def apply_automatic_progression(self):
        self.ensure_tracking_state(save=True)

        while (
            self.status not in TERMINAL_ORDER_STATUSES
            and self.next_auto_status_at
            and self.next_auto_status_at <= timezone.now()
        ):
            rule = self.get_active_automation_rule()
            if not rule:
                self.next_auto_status_at = None
                type(self).objects.filter(pk=self.pk).update(next_auto_status_at=None)
                break

            self.advance_status(
                new_status=rule.to_status,
                is_automatic=True,
                note=rule.admin_note or f"Automatically updated after {rule.delay_minutes} minutes.",
                customer_message=rule.customer_message,
            )

    def get_tracking_data(self):
        self.apply_automatic_progression()
        self.refresh_from_db()

        active_rule = self.get_active_automation_rule()
        seconds_until_next_status = None
        cancel_deadline = self.get_customer_cancel_deadline()
        tracking_visibility_deadline = self.get_tracking_visibility_deadline()
        seconds_until_tracking_expires = None

        if self.next_auto_status_at:
            seconds_until_next_status = max(
                0,
                int((self.next_auto_status_at - timezone.now()).total_seconds()),
            )

        if tracking_visibility_deadline:
            seconds_until_tracking_expires = max(
                0,
                int((tracking_visibility_deadline - timezone.now()).total_seconds()),
            )

        return {
            "order_number": self.order_number,
            "tracking_id": str(self.tracking_id),
            "order_id": self.id,
            "order_status": self.status,
            "order_status_label": self.get_status_display(),
            "status_message": self.get_status_message(),
            "delivered_message": self.get_delivered_message(),
            "is_terminal": self.status in TERMINAL_ORDER_STATUSES,
            "can_customer_cancel": self.can_customer_cancel(),
            "cancel_deadline": cancel_deadline.isoformat() if cancel_deadline else None,
            "tracking_visible": self.is_tracking_visible_to_customer(),
            "tracking_visibility_deadline": tracking_visibility_deadline.isoformat() if tracking_visibility_deadline else None,
            "seconds_until_tracking_expires": seconds_until_tracking_expires,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status_updated_at": self.status_updated_at.isoformat() if self.status_updated_at else None,
            "next_auto_status_at": self.next_auto_status_at.isoformat() if self.next_auto_status_at else None,
            "next_status": active_rule.to_status if active_rule else "",
            "next_status_label": active_rule.get_to_status_display() if active_rule else "",
            "seconds_until_next_status": seconds_until_next_status,
            "items": [
                {
                    "name": item.name,
                    "size": item.size,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "line_total": float(item.price * item.quantity),
                }
                for item in self.items.all()
            ],
            "timeline": [
                {
                    "status": item.status,
                    "status_label": item.get_status_display(),
                    "previous_status": item.previous_status,
                    "is_automatic": item.is_automatic,
                    "note": item.note,
                    "customer_message": item.customer_message,
                    "changed_at": item.changed_at.isoformat(),
                }
                for item in self.status_history.all().order_by("-changed_at")
            ],
        }


    def __str__(self):
        return f"Order #{self.id} - {self.status}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    name = models.CharField(max_length=100)

    size = models.CharField(max_length=20)

    price = models.DecimalField(max_digits=6, decimal_places=2)

    quantity = models.IntegerField()

    def __str__(self):
        return self.name


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history"
    )
    previous_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_updates"
    )
    is_automatic = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True)
    customer_message = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["changed_at"]
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status History"

    def __str__(self):
        return f"Order #{self.order_id} - {self.get_status_display()}"


class SiteSettings(models.Model):
    THEME_CHOICES = (
        ("default", "Default"),
        ("light", "Light"),
        ("olive", "Olive"),
        ("sunset", "Sunset"),
    )

    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=8
    )

    delivery_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=110
    )

    free_delivery_threshold = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=5000
    )   

    # discount for ALL users (used only if no special discount)
    global_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    # extra discount only for logged-in users
    auth_user_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    # limited-time discount
    special_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    special_discount_start = models.DateTimeField(null=True, blank=True)
    special_discount_end = models.DateTimeField(null=True, blank=True)
    customer_cancel_window_minutes = models.PositiveIntegerField(
        default=2,
        help_text="Customers can cancel their order only within this many minutes after placing it.",
    )
    tracking_visibility_after_delivery_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Keep delivered orders visible in customer tracking for this many minutes after delivery.",
    )
    tracking_visibility_after_cancellation_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Keep cancelled orders visible in customer tracking for this many minutes after cancellation.",
    )
    active_theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default="default",
        help_text="Theme applied across the customer-facing website.",
    )
    chat_is_enabled = models.BooleanField(
        default=True,
        help_text="Enable or disable customer live chat on the website.",
    )
    chat_auto_response = models.TextField(
        blank=True,
        default="Thanks for reaching out. Our team will reply shortly.",
        help_text="This message is sent once automatically when a customer starts a new chat.",
    )

    # 🔥 Only ONE instance allowed
    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise Exception("You can only have ONE Site Settings instance.")
        return super().save(*args, **kwargs)

    # ✅ Check if special discount is active
    def special_discount_active(self):
        now = timezone.now()
        if self.special_discount_start and self.special_discount_end:
            return self.special_discount_start <= now <= self.special_discount_end
        return False

    # ✅ Get active discount percent (automatically ignores global)
    def get_active_discount_percent(self, user=None):
        discount = Decimal("0.00")

        # Priority 1: Special Discount
        if self.special_discount_active():
            discount += self.special_discount_percent
        else:
            discount += self.global_discount_percent

        # Extra for logged-in users
        if user and user.is_authenticated:
            discount += self.auth_user_discount_percent

        return discount

    def __str__(self):
        return "Main Site Settings"

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"


class LiveChatThread(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="live_chat_threads",
    )
    session_key = models.CharField(max_length=40, db_index=True)
    display_name = models.CharField(max_length=120, default="Anonymous User")
    is_authenticated_user = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-last_message_at", "-updated_at"]
        verbose_name = "Live Chat Thread"
        verbose_name_plural = "Live Chat Threads"

    def __str__(self):
        status = "Logged-in" if self.is_authenticated_user else "Anonymous"
        return f"{self.display_name} ({status})"


class LiveChatMessage(models.Model):
    SENDER_CUSTOMER = "customer"
    SENDER_ADMIN = "admin"
    SENDER_SYSTEM = "system"
    SENDER_CHOICES = (
        (SENDER_CUSTOMER, "Customer"),
        (SENDER_ADMIN, "Support"),
        (SENDER_SYSTEM, "Auto"),
    )

    thread = models.ForeignKey(
        LiveChatThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message_text = models.TextField(max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "Live Chat Message"
        verbose_name_plural = "Live Chat Messages"

    def __str__(self):
        return f"{self.get_sender_type_display()} - {self.thread.display_name}"
