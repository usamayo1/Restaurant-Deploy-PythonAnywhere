document.addEventListener("DOMContentLoaded", function () {

    console.log("menu.js loaded");

    const menu = document.querySelector('.menu-bar');
    const leftBtn = document.querySelector('.scroll-btn.left');
    const rightBtn = document.querySelector('.scroll-btn.right');

    if (menu && leftBtn && rightBtn) {

        rightBtn.addEventListener('click', () => {
            menu.scrollBy({ left: 200, behavior: 'smooth' });
        });

        leftBtn.addEventListener('click', () => {
            menu.scrollBy({ left: -200, behavior: 'smooth' });
        });

    }

});


// To Active(means change bg color) a tag(Button) of Menu Bar


/* Select only menu links that actually target an id (href starts with '#') */
const menuLinks = Array.from(document.querySelectorAll('.menu-bar a[href^="#"]'));

/* Build a map of id -> link for quick lookup */
const idToLink = {};
menuLinks.forEach(link => {
  const id = link.getAttribute('href').slice(1); // remove leading '#'
  if (!id) return;
  const targetEl = document.getElementById(id);
  if (!targetEl) return; // skip if target doesn't exist on the page
  idToLink[id] = { link, targetEl };

  /* Click: add active immediately (and allow native smooth scrolling) */
  link.addEventListener('click', (e) => {
    // remove active from all
    menuLinks.forEach(l => l.classList.remove('active'));
    link.classList.add('active');
    // native anchor behaviour will scroll; no preventDefault needed
  });
});

/* IntersectionObserver: highlight link when its target is in view */
const observerOptions = {
  root: null,
  // tune these values (top offset) to match when you want the link to activate
  // negative top margin makes entry happen earlier, negative bottom makes it leave earlier
  rootMargin: '-25% 0px -50% 0px',
  threshold: 0
};

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    const id = entry.target.id;
    const data = idToLink[id];
    if (!data) return;

    if (entry.isIntersecting) {
      // remove active from all then set current
      menuLinks.forEach(l => l.classList.remove('active'));
      data.link.classList.add('active');
      // Optional: set aria-current for accessibility
      menuLinks.forEach(l => l.removeAttribute('aria-current'));
      data.link.setAttribute('aria-current', 'true');
    }
  });
}, observerOptions);

/* Observe all existing targets */
Object.values(idToLink).forEach(item => observer.observe(item.targetEl));





//////// ///////////

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


// For The Add to Cart Price and Etc . 



let selectedVariant = null;
let quantity = 1;

/* OPEN POPUP */
document.querySelectorAll(".open-cart").forEach(button => {
    button.addEventListener("click", function() {

        selectedVariant = null;
        quantity = 1;
        document.querySelector(".count").innerText = 1;

        const itemName = this.dataset.itemName;
        const itemImage = this.dataset.itemImage;
        let variants = [];
        try {
            variants = JSON.parse(this.dataset.variants || "[]");
        } catch (error) {
            variants = [];
        }

        // Set name
        document.querySelector(".cart-content h4").innerText = itemName;

        // Set image
        document.querySelector(".top-div img").src = itemImage;

        const wrapper = document.querySelector(".variants-wrapper");
        const addToCartButton = document.querySelector(".cart-content .cart-btn1");
        wrapper.innerHTML = "";

        if (!Array.isArray(variants) || variants.length === 0) {
            if (addToCartButton) {
                addToCartButton.disabled = true;
            }
            wrapper.innerHTML = `<p class="variant-empty">No size options available for this item.</p>`;
            document.querySelector(".cart-section").classList.add("active");
            return;
        }

        if (addToCartButton) {
            addToCartButton.disabled = false;
        }

        variants.forEach((variant, index) => {

            wrapper.innerHTML += `
                <div class="size">
                    <div class="size-detail">
                        <input type="radio" name="size" value="${variant.id}" ${index === 0 ? "checked" : ""}>
                        <h5>${variant.size}</h5>
                    </div>
                    <p>Rs. ${variant.price}</p>
                </div>
            `;

            if(index === 0){
                selectedVariant = variant.id;
            }
        });

        // Radio change
        document.querySelectorAll('input[name="size"]').forEach(radio => {
            radio.addEventListener("change", function(){
                selectedVariant = this.value;
            });
        });

        document.querySelector(".cart-section").classList.add("active");
    });
});

/* CLOSE */
const closeCartBtn = document.querySelector(".close-cart");
const cartSection = document.querySelector(".cart-section");

if (closeCartBtn && cartSection) {
    closeCartBtn.addEventListener("click", function () {
        cartSection.classList.remove("active");
    });
}


/* INCREASE */
// let quantity = 1;

const increaseBtn = document.querySelector(".increase");
const countDisplay = document.querySelector(".count");

if (increaseBtn && countDisplay) {
    increaseBtn.addEventListener("click", function () {
        quantity++;
        countDisplay.innerText = quantity;
    });
}

/* DECREASE */
const decreaseBtn = document.querySelector(".decrease");

if (decreaseBtn && countDisplay) {
    decreaseBtn.addEventListener("click", function () {
        if (quantity > 1) {
            quantity--;
            countDisplay.innerText = quantity;
        }
    });
}

/* ADD TO CART */
/* ADD TO CART (POPUP CONFIRM BUTTON) */

document.addEventListener("click", function(e){

    if(e.target.matches(".cart-content .cart-btn1")){

        e.preventDefault();
        if (!selectedVariant) {
            showToast("Please choose a size first");
            return;
        }

        const csrftoken = getCookie("csrftoken");

        fetch("/add-to-cart/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": csrftoken
            },
            body: new URLSearchParams({
                variant_id: String(selectedVariant),
                quantity: String(quantity),
            }).toString()
        })
        .then(response => response.json())
        .then(data => {

            updateCartCount(data.cart_count);
            if(data.status === "success"){

                showToast("Added to cart ✓");

            }
            else if(data.status === "exists"){

                showToast("Quantity updated ✓");

            }

            document.querySelector(".cart-section").classList.remove("active");

        });

    }

});
