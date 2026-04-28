from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Category,
    DailyDeal,
    Item,
    ItemVariant,
    Order,
    OrderItem,
    OrderStatusAutomationRule,
    OurSpecial,
    PopularDeal,
    PopularDealsSection,
    SiteSettings,
)


class CoreOrderFlowTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.settings = SiteSettings.objects.create(
            tax_percent=Decimal("8.00"),
            delivery_fee=Decimal("110.00"),
            free_delivery_threshold=Decimal("5000.00"),
            customer_cancel_window_minutes=5,
            tracking_visibility_after_delivery_minutes=1,
            tracking_visibility_after_cancellation_minutes=1,
        )

        self.category = Category.objects.create(name="Burger")
        self.item = Item.objects.create(name="Zinger", category=self.category)
        self.variant = ItemVariant.objects.create(
            item=self.item,
            size="Regular",
            price=Decimal("450.00"),
        )

        self.daily_deal = DailyDeal.objects.create(title="Daily Deal", price=Decimal("900.00"))
        self.popular_section = PopularDealsSection.objects.create(title="Popular")
        self.popular_deal = PopularDeal.objects.create(
            section=self.popular_section,
            title="Popular Combo",
            description="Combo",
            price=Decimal("1200.00"),
            image="popular_deals/test.jpg",
        )
        self.special = OurSpecial.objects.create(
            main_image="our_special/test.jpg",
            description="Chef special",
            price=Decimal("1500.00"),
        )

    def _set_cart(self, cart_data):
        session = self.client.session
        session["cart"] = cart_data
        session.save()

    def _set_guest_tracking(self, order):
        session = self.client.session
        session["guest_tracking_ids"] = [str(order.tracking_id)]
        session["last_tracking_id"] = str(order.tracking_id)
        session.save()

    def test_add_to_cart_requires_post(self):
        response = self.client.get(reverse("add_to_cart"))
        self.assertEqual(response.status_code, 405)

    def test_health_check_endpoint(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_add_to_cart_rejects_invalid_quantity(self):
        response = self.client.post(
            reverse("add_to_cart"),
            {"variant_id": self.variant.id, "quantity": 0},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    def test_add_to_cart_success_updates_session(self):
        response = self.client.post(
            reverse("add_to_cart"),
            {"variant_id": self.variant.id, "quantity": 2},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["cart_count"], 2)

        session_cart = self.client.session.get("cart", {})
        self.assertIn(str(self.variant.id), session_cart)
        self.assertEqual(session_cart[str(self.variant.id)]["quantity"], 2)

    def test_mutating_cart_endpoints_require_post(self):
        response_update = self.client.get(reverse("update_cart", args=[self.variant.id, "increase"]))
        response_remove = self.client.get(reverse("remove_cart_item", args=[self.variant.id]))
        response_daily = self.client.get(reverse("add_daily_deal", args=[self.daily_deal.id]))
        response_popular = self.client.get(reverse("add_popular_deal", args=[self.popular_deal.id]))
        response_special = self.client.get(reverse("add_special", args=[self.special.id]))

        self.assertEqual(response_update.status_code, 405)
        self.assertEqual(response_remove.status_code, 405)
        self.assertEqual(response_daily.status_code, 405)
        self.assertEqual(response_popular.status_code, 405)
        self.assertEqual(response_special.status_code, 405)

    def test_cart_totals_works_without_crash(self):
        self._set_cart({
            str(self.variant.id): {
                "name": "Zinger",
                "image": "",
                "size": "Regular",
                "price": 450.0,
                "quantity": 1,
            }
        })
        response = self.client.get(reverse("cart_totals"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("total", payload)
        self.assertIn("tax", payload)

    def test_checkout_route_redirects_to_cart(self):
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("Cart"))

    def test_place_order_requires_post(self):
        response = self.client.get(reverse("place_order"))
        self.assertEqual(response.status_code, 405)

    def test_place_order_validates_address(self):
        self._set_cart({
            str(self.variant.id): {
                "name": "Zinger",
                "image": "",
                "size": "Regular",
                "price": 450.0,
                "quantity": 1,
            }
        })
        response = self.client.post(reverse("place_order"), {
            "name": "Guest User",
            "phone": "03000000000",
            "address": "",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Address is required")

    def test_place_order_creates_order_items_and_clears_cart(self):
        self._set_cart({
            str(self.variant.id): {
                "name": "Zinger",
                "image": "",
                "size": "Regular",
                "price": 450.0,
                "quantity": 2,
            }
        })

        response = self.client.post(reverse("place_order"), {
            "name": "Guest User",
            "email": "guest@example.com",
            "phone": "03000000000",
            "address": "Johar Town",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        order = Order.objects.get()
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertEqual(self.client.session.get("cart", {}), {})
        self.assertIn(str(order.tracking_id), self.client.session.get("guest_tracking_ids", []))

    def test_track_order_forbidden_for_non_owner(self):
        user = User.objects.create_user(username="owner", password="pass12345")
        order = Order.objects.create(
            user=user,
            name="Owner",
            email="owner@example.com",
            phone="03000000000",
            address="Address",
            total=Decimal("999.00"),
        )
        order.initialize_tracking()

        response = self.client.get(reverse("track_order", args=[order.tracking_id]))
        self.assertEqual(response.status_code, 403)

    def test_track_order_allows_guest_owner(self):
        order = Order.objects.create(
            name="Guest",
            email="guest@example.com",
            phone="03000000000",
            address="Address",
            total=Decimal("999.00"),
        )
        order.initialize_tracking()
        self._set_guest_tracking(order)

        response = self.client.get(reverse("track_order", args=[order.tracking_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_cancel_order_requires_post(self):
        order = Order.objects.create(
            name="Guest",
            email="guest@example.com",
            phone="03000000000",
            address="Address",
            total=Decimal("999.00"),
        )
        order.initialize_tracking()
        self._set_guest_tracking(order)

        response = self.client.get(reverse("cancel_order", args=[order.tracking_id]))
        self.assertEqual(response.status_code, 405)

    def test_cancel_order_forbidden_for_non_owner(self):
        order = Order.objects.create(
            name="Guest",
            email="guest@example.com",
            phone="03000000000",
            address="Address",
            total=Decimal("999.00"),
        )
        order.initialize_tracking()

        response = self.client.post(reverse("cancel_order", args=[order.tracking_id]))
        self.assertEqual(response.status_code, 403)

    def test_cancel_order_for_guest_owner(self):
        order = Order.objects.create(
            name="Guest",
            email="guest@example.com",
            phone="03000000000",
            address="Address",
            total=Decimal("999.00"),
        )
        order.initialize_tracking()
        self._set_guest_tracking(order)

        response = self.client.post(reverse("cancel_order", args=[order.tracking_id]))
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")

    def test_tracking_visibility_expired_returns_410(self):
        order = Order.objects.create(
            name="Guest",
            email="guest@example.com",
            phone="03000000000",
            address="Address",
            total=Decimal("999.00"),
        )
        order.initialize_tracking()
        delivered_at = timezone.now() - timedelta(minutes=5)
        order.advance_status(
            new_status="delivered",
            changed_at=delivered_at,
            customer_message="Delivered",
        )
        self._set_guest_tracking(order)

        response = self.client.get(reverse("track_order", args=[order.tracking_id]))
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()["status"], "expired")

    def test_automatic_status_progression_on_tracking(self):
        OrderStatusAutomationRule.objects.update_or_create(
            from_status="pending",
            defaults={
                "to_status": "confirmed",
                "delay_minutes": 0,
                "is_active": True,
                "customer_message": "Auto confirmed",
            },
        )
        order = Order.objects.create(
            name="Guest",
            email="guest@example.com",
            phone="03000000000",
            address="Address",
            total=Decimal("999.00"),
        )
        order.initialize_tracking()
        self._set_guest_tracking(order)

        response = self.client.get(reverse("track_order", args=[order.tracking_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["order_status"], "confirmed")
