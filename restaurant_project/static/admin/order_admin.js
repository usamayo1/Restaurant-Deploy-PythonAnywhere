function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.quickOrderStatusUpdate = async function (triggerElement) {
    const csrftoken = getCookie("csrftoken");
    const wrapper = triggerElement.closest(".status-control");
    const selectField = wrapper?.querySelector(".quick-status-select");
    const feedback = wrapper?.querySelector(".status-update-feedback");
    const button = wrapper?.querySelector(".quick-status-button");
    const statusUrl = selectField?.dataset.statusUrl;
    const previousValue = selectField?.dataset.previousValue || selectField?.value;

    if (!statusUrl || !feedback || !selectField || !button) {
        return;
    }

    selectField.disabled = true;
    button.disabled = true;
    feedback.textContent = "Saving...";
    feedback.className = "status-update-feedback is-saving";

    try {
        const response = await fetch(statusUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken,
            },
            body: JSON.stringify({ status: selectField.value }),
        });

        const data = await response.json();

        if (!response.ok || data.status !== "success") {
            throw new Error(data.message || "Unable to update status.");
        }

        selectField.dataset.previousValue = data.order_status;
        selectField.value = data.order_status;
        wrapper.className = `status-control status-${data.order_status}`;
        feedback.textContent = `${data.message} ${data.updated_at}`;
        feedback.className = "status-update-feedback is-success";

        const row = selectField.closest("tr");
        const updatedCell = row?.querySelector(".field-status_updated_at");
        if (updatedCell) {
            updatedCell.textContent = data.updated_at;
        }
    } catch (error) {
        selectField.value = previousValue;
        feedback.textContent = error.message || "Update failed.";
        feedback.className = "status-update-feedback is-error";
        alert(error.message || "Update failed.");
    } finally {
        selectField.disabled = false;
        button.disabled = false;
        setTimeout(() => {
            if (feedback.classList.contains("is-success")) {
                feedback.textContent = "Saved";
            }
        }, 1200);
    }
};

document.addEventListener("DOMContentLoaded", function () {
    function initializeTopResultsScroller() {
        const resultsNode = document.querySelector("#changelist .results");
        const tableNode = resultsNode?.querySelector("table");

        if (!resultsNode || !tableNode) {
            return;
        }

        const host = document.createElement("div");
        host.className = "order-top-scroll-host";
        host.innerHTML = `
            <div class="order-top-scroll-head">
                <span>Scroll orders horizontally</span>
            </div>
            <div class="order-top-scroll-track" aria-hidden="true">
                <div class="order-top-scroll-fill"></div>
            </div>
        `;

        resultsNode.parentNode.insertBefore(host, resultsNode);

        const topScroller = host.querySelector(".order-top-scroll-track");
        const topFill = host.querySelector(".order-top-scroll-fill");
        let syncing = false;

        function refreshScrollerWidth() {
            const hasOverflow = tableNode.scrollWidth > resultsNode.clientWidth;
            host.classList.toggle("is-hidden", !hasOverflow);
            topFill.style.width = `${tableNode.scrollWidth}px`;
        }

        topScroller.addEventListener("scroll", function () {
            if (syncing) {
                return;
            }
            syncing = true;
            resultsNode.scrollLeft = topScroller.scrollLeft;
            syncing = false;
        });

        resultsNode.addEventListener("scroll", function () {
            if (syncing) {
                return;
            }
            syncing = true;
            topScroller.scrollLeft = resultsNode.scrollLeft;
            syncing = false;
        });

        if (window.ResizeObserver) {
            const observer = new ResizeObserver(refreshScrollerWidth);
            observer.observe(resultsNode);
            observer.observe(tableNode);
        }

        window.addEventListener("resize", refreshScrollerWidth);
        refreshScrollerWidth();
    }

    initializeTopResultsScroller();

    document.querySelectorAll(".quick-status-select").forEach((selectField) => {
        selectField.dataset.previousValue = selectField.value;
        selectField.addEventListener("change", function () {
            const wrapper = this.closest(".status-control");
            const feedback = wrapper?.querySelector(".status-update-feedback");

            if (!feedback) {
                return;
            }

            if (this.value !== this.dataset.previousValue) {
                wrapper.className = `status-control status-${this.value}`;
                feedback.textContent = "Ready to update";
                feedback.className = "status-update-feedback is-pending";
            } else {
                wrapper.className = `status-control status-${this.dataset.previousValue}`;
                feedback.textContent = "";
                feedback.className = "status-update-feedback";
            }
        });
    });
});
