(function () {
  const navNode = document.querySelector(".admin-extra-nav[data-unread-url]");
  const badgeNode = document.getElementById("admin-live-chat-badge");

  if (!navNode || !badgeNode) {
    return;
  }

  const unreadUrl = navNode.dataset.unreadUrl;
  let timer = null;

  function setBadgeValue(count) {
    const parsedCount = Number(count || 0);
    const value = Number.isFinite(parsedCount) ? Math.max(0, parsedCount) : 0;

    if (value <= 0) {
      badgeNode.classList.add("is-hidden");
      badgeNode.textContent = "0";
      return;
    }

    badgeNode.classList.remove("is-hidden");
    badgeNode.textContent = value > 99 ? "99+" : String(value);
  }

  async function refreshUnreadCount() {
    try {
      const response = await fetch(unreadUrl, { method: "GET" });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      setBadgeValue(payload.unread_threads || 0);
    } catch (error) {
      return;
    }
  }

  refreshUnreadCount();
  timer = window.setInterval(refreshUnreadCount, 2500);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      refreshUnreadCount();
    }
  });

  window.addEventListener("beforeunload", () => {
    if (timer) {
      window.clearInterval(timer);
    }
  });
})();
