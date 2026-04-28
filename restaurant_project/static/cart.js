console.log("Cart.js is loading")

///// For the Popup of Added to Cart///

function showToast(message){
    const toast = document.getElementById("cart-toast");
    toast.innerText = message;
    toast.classList.add("show");

    setTimeout(()=>{
        toast.classList.remove("show");
    },2000);
}


//////////////////

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie("csrftoken");


/* ======================
UPDATE NAVBAR COUNT
====================== */
function updateCartCount(count){

    document.querySelectorAll(".cart-count").forEach(el=>{

        el.textContent = count;

        el.classList.add("bump");

        setTimeout(()=>{
            el.classList.remove("bump");
        },250); // same as CSS transition time

    });

}



/* ======================
   UPDATE QUANTITY
====================== */
document.querySelectorAll(".qty-btn").forEach(button => {
    button.addEventListener("click", function(){

        const id = this.dataset.id;
        const action = this.dataset.action;

        fetch(`/cart/update/${id}/${action}/`, {
            method: "POST",
            headers: { "X-CSRFToken": csrftoken }
        })
        .then(res => res.json())
        .then(data => {

            // update quantity
            document.getElementById(`qty-${id}`).innerText = data.quantity;

            // update item price
            document.getElementById(`price-${id}`).innerText =
                "Rs. " + data.item_total;

            // update ALL totals
            updateTotals(data);

            // keep all navbar cart badges in sync
            updateCartCount(data.cart_count);

        });
    });
});
/* ======================
   DELETE ITEM
====================== */
document.querySelectorAll(".delete-btn").forEach(button => {
    button.addEventListener("click", function(){

        const id = this.dataset.id;

        fetch(`/cart/remove/${id}/`, {
            method: "POST",
            headers: { "X-CSRFToken": csrftoken }
        })
        .then(res => res.json())
        .then(data => {

            this.closest(".product-cart").remove();

            updateTotals(data);

            updateCartCount(data.cart_count);

            // SHOW EMPTY CART MESSAGE
            if(data.cart_count === 0){
                clearCartUI();
            }

        });
    });
});

// function to update totals 

function updateTotals(data) {

    const safeUpdate = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.innerText = value;
    };

    safeUpdate("cart-subtotal", data.subtotal);
    safeUpdate("checkout-subtotal", data.subtotal);
    safeUpdate("checkout-tax", data.tax);
    safeUpdate("checkout-discount", data.discount);
    safeUpdate("checkout-delivery", data.delivery);
    safeUpdate("checkout-total", data.total);

    const discountRateEl = document.getElementById("checkout-discount-rate");
    if (discountRateEl) {
        if (data.discount_percent > 0) {
            discountRateEl.innerText = "(" + data.discount_percent + "%)";
            discountRateEl.style.display = "inline";
        } else {
            discountRateEl.style.display = "none";
        }
    }

    if (document.getElementById("checkout-saved")) {
    document.getElementById("checkout-saved").innerText =
        "You saved Rs." + data.you_saved + " on this order!";
    }

    const discountEl = document.getElementById("checkout-big-discount");

    if (discountEl) {
        if (data.discount_percent > 0) {
            discountEl.innerText =
                "🎉 " + data.discount_percent + "% OFF Applied!";
            discountEl.style.display = "block";
        } else {
            discountEl.style.display = "none";
        }
    }

    const savedEl = document.getElementById("checkout-saved");

    if (savedEl) {
        if (data.you_saved > 0) {
            savedEl.innerText =
                "You saved Rs." + data.you_saved + " on this order!";
            savedEl.style.display = "block";
        } else {
            savedEl.style.display = "none";
        }
    }

    // FREE DELIVERY MESSAGE
    // ----------------------------
    const freeDeliveryBox = document.getElementById("free-delivery-message");

    if (freeDeliveryBox) {

        if (data.free_delivery_qualified) {

            freeDeliveryBox.innerHTML =
                "🚚 You unlocked FREE delivery! (Saved Rs." +
                data.delivery_saved + ")";

            freeDeliveryBox.style.display = "block";

        } else if (data.amount_needed_for_free_delivery > 0) {

            freeDeliveryBox.innerHTML =
                "🛒 Add Rs." +
                data.amount_needed_for_free_delivery +
                " more to get FREE delivery!";

            freeDeliveryBox.style.display = "block";

        } else {
            freeDeliveryBox.style.display = "none";
        }
    }

    const specialOfferStatusRow = document.getElementById("special-offer-status-row");
    if (specialOfferStatusRow && data.special_discount_percent <= 0) {
        specialOfferStatusRow.style.display = "none";
    }

    const offerBox = document.getElementById("special-offer-box");
    if (offerBox && data.special_active === false) {
        offerBox.classList.add("hide-offer");
        setTimeout(() => {
            offerBox.remove();
        }, 500);
    }
}

function refreshCartTotalsAfterOfferExpiry() {
    fetch("/cart/totals/")
        .then(res => res.json())
        .then(data => {
            updateTotals(data);
        })
        .catch(() => {
        });
}

window.refreshCartTotalsAfterOfferExpiry = refreshCartTotalsAfterOfferExpiry;




/* ======================
DAILY DEAL
====================== */
document.querySelectorAll(".add-daily-deal")
.forEach(btn=>{

    btn.onclick=()=>{

        fetch(`/cart/add-daily-deal/${btn.dataset.id}/`,{
            method:"POST",
            headers:{
                "X-CSRFToken":csrftoken
            }
        })
        .then(r=>r.json())
        .then(data=>{

            updateCartCount(data.cart_count);

            if(data.status === "success"){
                showToast("Added to cart ✓");
            }

            if(data.status === "exists"){
                showToast("Already in cart");
            }

        })

    }

})


/* ======================
POPULAR DEAL
====================== */
document.querySelectorAll(".add-popular")
.forEach(btn=>{

    btn.onclick=()=>{

        fetch(`/cart/add-popular-deal/${btn.dataset.id}/`,{
            method:"POST",
            headers:{
                "X-CSRFToken":csrftoken
            }
        })
        .then(r=>r.json())
        .then(data=>{

            updateCartCount(data.cart_count);

            if(data.status === "success"){
                showToast("Added to cart ✓");
            }

            if(data.status === "exists"){
                showToast("Already in cart");
            }

        })

    }

})


/* ======================
OUR SPECIAL
====================== */
document.querySelectorAll(".add-special")
.forEach(btn=>{

    btn.onclick=()=>{

        fetch(`/cart/add-special/${btn.dataset.id}/`,{
            method:"POST",
            headers:{
                "X-CSRFToken":csrftoken
            }
        })
        .then(r=>r.json())
        .then(data=>{

            updateCartCount(data.cart_count);

            if(data.status === "success"){
                showToast("Added to cart ✓");
            }

            if(data.status === "exists"){
                showToast("Already in cart");
            }

        })

    }

})




// For The Checkout Section 

const checkoutBtn = document.querySelector(".checkout-btn");
const orderPopup = document.getElementById("orderPopup");
const trackOrderBtn = document.getElementById("trackOrderBtn");
const cancelOrderBtn = document.getElementById("cancelOrderBtn");
const trackingOrderList = document.getElementById("trackingOrderList");
const trackingOrderListWrap = document.getElementById("trackingOrderListWrap");

let trackingPollTimer = null;
let trackingCountdownTimer = null;
let trackingExpiryTimer = null;
let activeTrackingId = "";

function getEmptyCartMarkup() {
    return `
        <h2>Shopping Cart</h2>
        <div class="line">
            <div class="line-1"></div>
        </div>
        <p class="empty-cart">Your cart is empty.</p>
    `;
}

function clearCartUI() {
    const shopping = document.querySelector(".shopping");

    if (shopping) {
        shopping.innerHTML = getEmptyCartMarkup();
    }

    if (checkoutBtn) {
        checkoutBtn.disabled = true;
    }

    updateCartCount(0);
    updateTotals({
        subtotal: "0.00",
        tax: "0.00",
        discount: "0.00",
        delivery: "0.00",
        total: "0.00",
        you_saved: "0.00",
        discount_percent: 0,
        free_delivery_qualified: false,
        amount_needed_for_free_delivery: 0,
        delivery_saved: "0.00",
    });
}

function setActiveTrackingChip(trackingId) {
    if (!trackingOrderList) {
        return;
    }

    trackingOrderList.querySelectorAll(".tracking-order-chip").forEach((button) => {
        button.classList.toggle("is-active", button.dataset.trackingId === trackingId);
    });
}

function ensureTrackingOrderChip(trackingId, orderNumber) {
    if (!trackingOrderList || !trackingId) {
        return;
    }

    let existingButton = trackingOrderList.querySelector(`[data-tracking-id="${trackingId}"]`);

    if (!existingButton) {
        existingButton = document.createElement("button");
        existingButton.type = "button";
        existingButton.className = "tracking-order-chip";
        existingButton.dataset.trackingId = trackingId;
        existingButton.dataset.orderNumber = orderNumber || trackingId;
        existingButton.innerText = orderNumber || trackingId;
        trackingOrderList.prepend(existingButton);
    } else if (orderNumber) {
        existingButton.dataset.orderNumber = orderNumber;
        existingButton.innerText = orderNumber;
    }

    if (trackingOrderListWrap) {
        trackingOrderListWrap.style.display = "block";
    }
}

function removeTrackingOrderChip(trackingId) {
    if (!trackingOrderList || !trackingId) {
        return null;
    }

    const button = trackingOrderList.querySelector(`[data-tracking-id="${trackingId}"]`);
    if (button) {
        button.remove();
    }

    const remainingButtons = trackingOrderList.querySelectorAll(".tracking-order-chip");
    if (trackingOrderListWrap) {
        trackingOrderListWrap.style.display = remainingButtons.length ? "block" : "none";
    }

    return remainingButtons.length ? remainingButtons[0] : null;
}

function stopTrackingTimers() {
    if (trackingPollTimer) {
        clearInterval(trackingPollTimer);
        trackingPollTimer = null;
    }

    if (trackingCountdownTimer) {
        clearInterval(trackingCountdownTimer);
        trackingCountdownTimer = null;
    }

    if (trackingExpiryTimer) {
        clearInterval(trackingExpiryTimer);
        trackingExpiryTimer = null;
    }
}

function formatTrackingTime(isoValue) {
    if (!isoValue) {
        return "";
    }

    return new Date(isoValue).toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
    });
}

function formatCountdown(totalSeconds) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
        return `${hours}h ${minutes}m ${seconds}s`;
    }

    return `${minutes}m ${seconds}s`;
}

function startTrackingCountdown(seconds, nextStatusLabel) {
    const nextStepBox = document.getElementById("trackingNextStep");
    const nextStatusLabelEl = document.getElementById("nextStatusLabel");
    const nextStatusCountdownEl = document.getElementById("nextStatusCountdown");

    if (!nextStepBox || !nextStatusLabelEl || !nextStatusCountdownEl || seconds === null) {
        return;
    }

    let remaining = seconds;

    nextStepBox.style.display = "block";
    nextStatusLabelEl.innerText = nextStatusLabel;
    nextStatusCountdownEl.innerText = formatCountdown(remaining);

    trackingCountdownTimer = setInterval(() => {
        remaining -= 1;

        if (remaining <= 0) {
            nextStatusCountdownEl.innerText = "Updating...";
            clearInterval(trackingCountdownTimer);
            trackingCountdownTimer = null;
            return;
        }

        nextStatusCountdownEl.innerText = formatCountdown(remaining);
    }, 1000);
}

function startTrackingExpiryCountdown(seconds) {
    const expiryBox = document.getElementById("trackingExpiryBox");
    const expiryCountdownEl = document.getElementById("trackingExpiryCountdown");

    if (!expiryBox || !expiryCountdownEl || seconds === null) {
        return;
    }

    let remaining = seconds;
    expiryBox.style.display = "block";
    expiryCountdownEl.innerText = formatCountdown(remaining);

    trackingExpiryTimer = setInterval(() => {
        remaining -= 1;

        if (remaining <= 0) {
            expiryCountdownEl.innerText = "Closing...";
            clearInterval(trackingExpiryTimer);
            trackingExpiryTimer = null;
            handleTrackingExpired("This order is no longer available in customer tracking.");
            return;
        }

        expiryCountdownEl.innerText = formatCountdown(remaining);
    }, 1000);
}

function renderTrackingTimeline(timeline) {
    const trackingTimeline = document.getElementById("trackingTimeline");

    if (!trackingTimeline) {
        return;
    }

    if (!timeline || timeline.length === 0) {
        trackingTimeline.innerHTML = "<p class='tracking-step-note'>No tracking events yet.</p>";
        return;
    }

    trackingTimeline.innerHTML = timeline.map((item) => `
        <div class="tracking-step">
            <div class="tracking-step-head">
                <span class="tracking-step-status">${item.status_label}</span>
                <span class="tracking-step-time">${formatTrackingTime(item.changed_at)}</span>
            </div>
            <div class="tracking-step-note">${item.customer_message || item.note || ""}</div>
            <span class="tracking-step-mode">${item.is_automatic ? "Automatic update" : "Manual update"}</span>
        </div>
    `).join("");
}

function renderTrackingOrderDetails(items) {
    const orderDetails = document.getElementById("trackingOrderDetails");

    if (!orderDetails) {
        return;
    }

    if (!items || items.length === 0) {
        orderDetails.innerHTML = "<p class='tracking-step-note'>Order item details are not available.</p>";
        return;
    }

    orderDetails.innerHTML = items.map((item) => `
        <div class="tracking-order-item">
            <div class="tracking-order-item-main">
                <strong>${item.name}</strong>
                <span>${item.size} x ${item.quantity}</span>
            </div>
            <div class="tracking-order-item-price">Rs. ${item.line_total.toFixed(2)}</div>
        </div>
    `).join("");
}

function renderTrackingData(data) {
    const popupTitle = document.querySelector("#orderPopup .popup-content h2");
    const trackingIdEl = document.getElementById("trackingId");
    const orderNumberEl = document.getElementById("orderNumber");
    const orderStatusEl = document.getElementById("orderStatus");
    const trackingMessageEl = document.getElementById("trackingMessage");
    const deliveredMessageBox = document.getElementById("deliveredMessageBox");
    const nextStepBox = document.getElementById("trackingNextStep");
    const expiryBox = document.getElementById("trackingExpiryBox");
    const expiredBox = document.getElementById("trackingExpiredBox");

    if (popupTitle) {
        popupTitle.innerText = data.is_terminal ? "Order Tracking Update" : "Track Your Order";
    }

    orderNumberEl.innerText = data.order_number || "";
    trackingIdEl.innerText = data.tracking_id;
    orderStatusEl.innerText = data.order_status_label;
    orderStatusEl.className = `status-pill status-${data.order_status}`;
    trackingMessageEl.innerText = data.status_message || "";
    ensureTrackingOrderChip(data.tracking_id, data.order_number);
    setActiveTrackingChip(data.tracking_id);

    if (data.delivered_message) {
        deliveredMessageBox.innerText = data.delivered_message;
        deliveredMessageBox.style.display = "block";
    } else {
        deliveredMessageBox.style.display = "none";
        deliveredMessageBox.innerText = "";
    }

    if (expiredBox) {
        expiredBox.style.display = "none";
        expiredBox.innerText = "";
    }

    stopTrackingTimers();

    if (!data.is_terminal && data.seconds_until_next_status !== null) {
        startTrackingCountdown(data.seconds_until_next_status, data.next_status_label);
    } else if (nextStepBox) {
        nextStepBox.style.display = "none";
    }

    if (
        (data.order_status === "delivered" || data.order_status === "cancelled")
        && data.seconds_until_tracking_expires !== null
    ) {
        startTrackingExpiryCountdown(data.seconds_until_tracking_expires);
    } else if (expiryBox) {
        expiryBox.style.display = "none";
    }

    if (cancelOrderBtn) {
        if (data.can_customer_cancel) {
            cancelOrderBtn.style.display = "inline-flex";
            cancelOrderBtn.dataset.trackingId = data.tracking_id;
        } else {
            cancelOrderBtn.style.display = "none";
            cancelOrderBtn.dataset.trackingId = "";
        }
    }

    renderTrackingTimeline(data.timeline);
    renderTrackingOrderDetails(data.items);
}

function fetchTrackingData(trackingId) {
    return fetch(`/track-order/${trackingId}/`)
        .then((response) => response.json().then((data) => ({ response, data })))
        .then(({ response, data }) => {
            if (response.status === 410 || data.status === "expired") {
                const error = new Error(data.message || "Tracking is no longer available.");
                error.expired = true;
                throw error;
            }

            if (data.status !== "success") {
                throw new Error(data.message || "Failed to load tracking data");
            }

            renderTrackingData(data);

            if (!data.is_terminal) {
                trackingPollTimer = setInterval(() => {
                    fetchTrackingData(trackingId).catch((error) => {
                        if (error.expired) {
                            handleTrackingExpired(error.message);
                        } else {
                            stopTrackingTimers();
                        }
                    });
                }, 15000);
            }

            return data;
        });
}

function handleTrackingExpired(message) {
    const popupTitle = document.querySelector("#orderPopup .popup-content h2");
    const expiredBox = document.getElementById("trackingExpiredBox");
    const nextStepBox = document.getElementById("trackingNextStep");
    const expiryBox = document.getElementById("trackingExpiryBox");
    const deliveredMessageBox = document.getElementById("deliveredMessageBox");
    const trackingTimeline = document.getElementById("trackingTimeline");
    const trackingOrderDetails = document.getElementById("trackingOrderDetails");

    const expiredTrackingId = activeTrackingId;
    const fallbackButton = removeTrackingOrderChip(expiredTrackingId);

    stopTrackingTimers();

    if (popupTitle) {
        popupTitle.innerText = "Tracking Closed";
    }
    if (expiredBox) {
        expiredBox.innerText = message;
        expiredBox.style.display = "block";
    }
    if (nextStepBox) {
        nextStepBox.style.display = "none";
    }
    if (expiryBox) {
        expiryBox.style.display = "none";
    }
    if (deliveredMessageBox) {
        deliveredMessageBox.style.display = "none";
    }
    if (trackingTimeline) {
        trackingTimeline.innerHTML = "";
    }
    if (trackingOrderDetails) {
        trackingOrderDetails.innerHTML = "";
    }
    if (cancelOrderBtn) {
        cancelOrderBtn.style.display = "none";
    }
    if (fallbackButton) {
        openTrackingPopup(fallbackButton.dataset.trackingId);
        return;
    }
    if (trackOrderBtn) {
        trackOrderBtn.style.display = "none";
    }
}

function cancelTrackedOrder(trackingId) {
    if (!trackingId) {
        return;
    }

    fetch(`/cancel-order/${trackingId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken
        }
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.status !== "success") {
                throw new Error(data.message || "Unable to cancel order");
            }

            renderTrackingData(data);
            alert(data.message || "Order cancelled successfully.");
        })
        .catch((error) => {
            alert(error.message || "Unable to cancel order");
        });
}

function openTrackingPopup(trackingId) {
    if (!trackingId || !orderPopup) {
        return;
    }

    activeTrackingId = trackingId;
    orderPopup.style.display = "flex";
    setActiveTrackingChip(trackingId);

    fetchTrackingData(trackingId).catch((error) => {
        if (error.expired) {
            handleTrackingExpired(error.message || "Tracking is no longer available.");
            return;
        }
        alert(error.message || "Unable to load tracking details");
    });
}

if (checkoutBtn) {
checkoutBtn.addEventListener("click", function() {

    const csrftoken = getCookie("csrftoken");
    const nameValue = document.getElementById("name").value.trim();
    const emailValue = document.getElementById("email").value.trim();
    const phoneValue = document.getElementById("phone").value.trim();
    const addressValue = document.getElementById("address").value.trim();

    if (!nameValue) {
        alert("Please enter your full name.");
        document.getElementById("name").focus();
        return;
    }

    if (!phoneValue) {
        alert("Phone number is required before placing an order.");
        document.getElementById("phone").focus();
        return;
    }

    if (!addressValue) {
        alert("Address is required before placing an order.");
        document.getElementById("address").focus();
        return;
    }

    const formData = new FormData();
    formData.append("name", nameValue);
    formData.append("email", emailValue);
    formData.append("phone", phoneValue);
    formData.append("address", addressValue);

    fetch("/place-order/", {   // make sure URL matches your urls.py
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {

        if (data.status === "success") {
            clearCartUI();
            ensureTrackingOrderChip(data.tracking_id, data.order_number);
            if (trackOrderBtn) {
                trackOrderBtn.dataset.trackingId = data.tracking_id;
                trackOrderBtn.style.display = "inline-flex";
            }
            openTrackingPopup(data.tracking_id);

        } else {
            alert(data.message || "Something went wrong");
        }

    });

});
}

// To Close the popup of Tracking 

function closePopup(){
    stopTrackingTimers();
    activeTrackingId = "";
    document.getElementById("orderPopup").style.display = "none";
}

////////

function copyTracking(){

    const id = document.getElementById("trackingId").innerText;

    navigator.clipboard.writeText(id);

    alert("Tracking ID copied!");
}

// For Order Tracking open Btn 
trackOrderBtn?.addEventListener("click", function(){
    openTrackingPopup(this.dataset.trackingId);
});

cancelOrderBtn?.addEventListener("click", function() {
    const trackingId = this.dataset.trackingId || activeTrackingId;
    if (!trackingId) {
        return;
    }

    if (!window.confirm("Cancel this order now? This cannot be undone from customer tracking.")) {
        return;
    }

    cancelTrackedOrder(trackingId);
});

trackingOrderList?.addEventListener("click", function(event) {
    const button = event.target.closest(".tracking-order-chip");
    if (!button) {
        return;
    }

    openTrackingPopup(button.dataset.trackingId);
});
