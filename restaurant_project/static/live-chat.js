(function () {
  const widget = document.getElementById("live-chat-widget");
  if (!widget) {
    return;
  }

  const toggleButton = document.getElementById("live-chat-toggle");
  const closeButton = document.getElementById("live-chat-close");
  const panel = document.getElementById("live-chat-panel");
  const subtitle = document.getElementById("live-chat-subtitle");
  const messagesContainer = document.getElementById("live-chat-messages");
  const form = document.getElementById("live-chat-form");
  const input = document.getElementById("live-chat-input");
  const unreadBadge = document.getElementById("live-chat-unread");

  const bootstrapUrl = widget.dataset.bootstrapUrl;
  const messagesUrl = widget.dataset.messagesUrl;
  const sendUrl = widget.dataset.sendUrl;

  let threadId = null;
  let lastMessageId = 0;
  let lastSeenMessageId = 0;
  let isOpen = false;
  let pollTimer = null;
  let unreadCount = 0;

  function getCookie(name) {
    const cookieValue = `; ${document.cookie}`;
    const parts = cookieValue.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return "";
  }

  function escapeHtml(text) {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return String(text || "").replace(/[&<>"']/g, (char) => map[char]);
  }

  function formatTime(isoString) {
    if (!isoString) {
      return "";
    }
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) {
      return "";
    }
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function setUnreadCount(count) {
    unreadCount = Math.max(0, Number(count || 0));
    if (unreadCount === 0) {
      unreadBadge.classList.add("is-hidden");
      unreadBadge.textContent = "0";
      return;
    }
    unreadBadge.classList.remove("is-hidden");
    unreadBadge.textContent = unreadCount > 99 ? "99+" : String(unreadCount);
  }

  function getSeenStorageKey() {
    return `live_chat_seen_message_${threadId || "guest"}`;
  }

  function loadSeenMessageId() {
    try {
      const rawValue = localStorage.getItem(getSeenStorageKey());
      const parsed = Number(rawValue || 0);
      return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
    } catch (error) {
      return 0;
    }
  }

  function persistSeenMessageId(id) {
    try {
      localStorage.setItem(getSeenStorageKey(), String(Number(id || 0)));
    } catch (error) {
      return;
    }
  }

  function markAllMessagesAsRead() {
    lastSeenMessageId = Math.max(lastSeenMessageId, lastMessageId);
    persistSeenMessageId(lastSeenMessageId);
    setUnreadCount(0);
  }

  function isIncomingSupportMessage(message) {
    return !!message && !message.is_mine && message.sender_type !== "customer";
  }

  function appendMessage(message) {
    if (!message || !message.id) {
      return;
    }

    if (message.id > lastMessageId) {
      lastMessageId = message.id;
    }

    const emptyState = messagesContainer.querySelector(".live-chat-empty");
    if (emptyState) {
      emptyState.remove();
    }

    const isMine = !!message.is_mine;
    const wrapper = document.createElement("article");
    wrapper.className = `live-chat-bubble ${isMine ? "mine" : "other"}`;
    wrapper.dataset.messageId = String(message.id);
    wrapper.innerHTML = `
      <div class="meta">
        <span>${escapeHtml(message.sender_label || "")}</span>
        <time>${escapeHtml(formatTime(message.created_at))}</time>
      </div>
      <div class="text">${escapeHtml(message.message_text || "")}</div>
    `;
    messagesContainer.appendChild(wrapper);
  }

  function renderMessages(messages, reset, shouldCountUnread) {
    if (reset) {
      messagesContainer.innerHTML = "";
      lastMessageId = 0;
    }

    const existingIds = new Set(
      Array.from(messagesContainer.querySelectorAll(".live-chat-bubble")).map((node) => Number(node.dataset.messageId))
    );
    let addedCount = 0;

    (messages || []).forEach((message) => {
      if (existingIds.has(Number(message.id))) {
        return;
      }
      appendMessage(message);
      addedCount += 1;
      if (shouldCountUnread && !isOpen && isIncomingSupportMessage(message) && message.id > lastSeenMessageId) {
        setUnreadCount(unreadCount + 1);
      }
    });

    if (!messagesContainer.children.length) {
      messagesContainer.innerHTML = `<p class="live-chat-empty">Start a conversation with support.</p>`;
      return;
    }

    if (reset || addedCount > 0) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  async function requestJson(url, options) {
    const response = await fetch(url, options);
    let payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = null;
    }
    if (!response.ok) {
      const message = payload && payload.message ? payload.message : "Request failed.";
      throw new Error(message);
    }
    return payload || {};
  }

  async function bootstrapChat() {
    try {
      const payload = await requestJson(bootstrapUrl, { method: "GET" });
      if (!payload.chat_enabled) {
        widget.classList.add("is-hidden");
        return;
      }
      widget.classList.remove("is-hidden");
      const thread = payload.thread || {};
      threadId = Number(thread.id || 0) || null;
      lastSeenMessageId = loadSeenMessageId();
      subtitle.textContent = thread.display_name
        ? `You are chatting as ${thread.display_name}`
        : "We usually reply quickly.";
      renderMessages(payload.messages || [], true, false);
      if (payload.last_message_id) {
        lastMessageId = payload.last_message_id;
      }
      const unseenSupportMessages = (payload.messages || []).filter(
        (message) => isIncomingSupportMessage(message) && message.id > lastSeenMessageId
      ).length;
      setUnreadCount(unseenSupportMessages);
    } catch (error) {
      widget.classList.add("is-hidden");
    }
  }

  async function pollMessages() {
    try {
      const separator = messagesUrl.includes("?") ? "&" : "?";
      const payload = await requestJson(`${messagesUrl}${separator}since_id=${encodeURIComponent(lastMessageId)}`, {
        method: "GET",
      });
      if (!payload.chat_enabled) {
        widget.classList.add("is-hidden");
        return;
      }
      renderMessages(payload.messages || [], false, true);
      if (payload.last_message_id && payload.last_message_id > lastMessageId) {
        lastMessageId = payload.last_message_id;
      }
      if (isOpen) {
        markAllMessagesAsRead();
      }
    } catch (error) {
      return;
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) {
      return;
    }

    input.disabled = true;
    form.querySelector("button").disabled = true;
    try {
      const payload = await requestJson(sendUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ message: text }),
      });
      input.value = "";
      if (payload.messages && payload.messages.length) {
        renderMessages(payload.messages, false, false);
      } else if (payload.message) {
        renderMessages([payload.message], false, false);
      }
      markAllMessagesAsRead();
    } catch (error) {
      return;
    } finally {
      input.disabled = false;
      form.querySelector("button").disabled = false;
      input.focus();
    }
  }

  function openPanel() {
    widget.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    isOpen = true;
    markAllMessagesAsRead();
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    input.focus();
  }

  function closePanel() {
    widget.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
    isOpen = false;
  }

  toggleButton.addEventListener("click", () => {
    if (isOpen) {
      closePanel();
      return;
    }
    openPanel();
  });

  closeButton.addEventListener("click", closePanel);
  form.addEventListener("submit", sendMessage);

  bootstrapChat().then(() => {
    if (pollTimer) {
      window.clearInterval(pollTimer);
    }
    pollTimer = window.setInterval(pollMessages, 3000);
  });
})();
