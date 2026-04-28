// Slider on Food Items Section 
console.log("Home JS is loaded")

function setupHorizontalSlider(trackSelector, leftSelector, rightSelector, options = {}) {
    const track = document.querySelector(trackSelector);
    const leftButton = document.querySelector(leftSelector);
    const rightButton = document.querySelector(rightSelector);

    if (!track || !leftButton || !rightButton) {
        return;
    }

    const getStep = () => {
        if (options.step) {
            return options.step;
        }

        const firstCard = track.querySelector(options.itemSelector || ".item, .f-card");
        if (!firstCard) {
            return 260;
        }

        const gap = Number.parseFloat(window.getComputedStyle(track).gap || "0");
        return firstCard.getBoundingClientRect().width + gap;
    };

    leftButton.addEventListener("click", () => {
        track.scrollBy({ left: -getStep(), behavior: "smooth" });
    });

    rightButton.addEventListener("click", () => {
        track.scrollBy({ left: getStep(), behavior: "smooth" });
    });
}

setupHorizontalSlider(".food-items", ".go-left", ".go-right", { itemSelector: ".item" });
setupHorizontalSlider(".feedbacks", ".lefty", ".righty", { itemSelector: ".f-card" });
setupHorizontalSlider(".fav-food", ".popular-left", ".popular-right", { itemSelector: ".item" });


// For the NavBar links to not reload page to click 

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {

        const section = this.getAttribute('data-section');

        if (section) {
            // If already on homepage
            if (window.location.pathname === "/") {
                e.preventDefault();
                document.getElementById(section).scrollIntoView({
                    behavior: 'smooth'
                });
            } else {
                // Go to homepage with section
                window.location.href = "/#" + section;
            }
        }

    });
});


