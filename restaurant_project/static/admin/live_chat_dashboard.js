(function () {
  const root = document.getElementById("live-chat-admin-dashboard");
  if (!root) {
    return;
  }

  const threadsUrl = root.dataset.threadsUrl;
  const messagesTemplate = root.dataset.messagesUrlTemplate;
  const sendTemplate = root.dataset.sendUrlTemplate;

  const threadListNode = document.getElementById("chat-thread-list");
  const searchInput = document.getElementById("chat-thread-search");
  const headerNode = document.getElementById("chat-thread-header");
  const messagesNode = document.getElementById("chat-admin-messages");
  const form = document.getElementById("chat-admin-form");
  const input = document.getElementById("chat-admin-input");

  let activeThreadId = null;
  let lastMessageId = 0;
  let pollTimer = null;
  let searchDebounce = null;

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
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
    const value = new Date(isoString);
    if (Number.isNaN(value.getTime())) {
      return "";
    }
    return value.toLocaleString([], {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  async function requestJson(url, options) {
    const response = await fetch(url, options);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.message || "Request failed.");
    }
    return payload;
  }

  function buildMessagesUrl(threadId, sinceId) {
    return messagesTemplate.replace("/0/", `/${threadId}/`) + `?since_id=${encodeURIComponent(sinceId || 0)}`;
  }

  function buildSendUrl(threadId) {
    return sendTemplate.replace("/0/", `/${threadId}/`);
  }

  function renderThreadList(threads) {
    if (!threads.length) {
      threadListNode.innerHTML = `<p class="chat-admin-empty">No conversations found.</p>`;
      return;
    }

    threadListNode.innerHTML = threads
      .map((thread) => {
        const unread = Number(thread.unread_count || 0);
        const preview = thread.last_message_text ? thread.last_message_text : "No messages yet.";
        const visitorType = thread.is_authenticated_user ? "Logged in" : "Anonymous";
        return `
          <button class="chat-thread-item ${thread.id === activeThreadId ? "is-active" : ""}" data-thread-id="${thread.id}">
            <div class="row">
              <span class="name">${escapeHtml(thread.display_name || "User")}</span>
              <span class="time">${escapeHtml(formatTime(thread.last_message_at))}</span>
            </div>
            <div class="meta">
              <span>${visitorType}</span>
              ${unread > 0 ? `<span class="chat-unread-count">${unread}</span>` : ""}
            </div>
            <p class="preview">${escapeHtml(preview)}</p>
          </button>
        `;
      })
      .join("");

    threadListNode.querySelectorAll(".chat-thread-item").forEach((item) => {
      item.addEventListener("click", () => {
        const threadId = Number(item.dataset.threadId);
        if (!threadId) {
          return;
        }
        openThread(threadId);
      });
    });
  }

  function renderMessageBubble(message, appendOnly) {
    if (!appendOnly) {
      messagesNode.innerHTML = "";
    }

    const existing = messagesNode.querySelector(`[data-message-id="${message.id}"]`);
    if (existing) {
      return;
    }

    const emptyState = messagesNode.querySelector(".chat-admin-empty");
    if (emptyState) {
      emptyState.remove();
    }

    const isAdmin = message.sender_type === "admin";
    const bubble = document.createElement("article");
    bubble.className = `chat-msg ${isAdmin ? "admin" : "other"}`;
    bubble.dataset.messageId = String(message.id);
    bubble.innerHTML = `
      <div class="meta">
        <span>${escapeHtml(message.sender_label || "")}</span>
        <time>${escapeHtml(formatTime(message.created_at))}</time>
      </div>
      <div class="text">${escapeHtml(message.message_text || "")}</div>
    `;
    messagesNode.appendChild(bubble);
  }

  function renderMessages(messages, reset) {
    if (reset) {
      messagesNode.innerHTML = "";
      lastMessageId = 0;
    }
    if (!messages.length && reset) {
      messagesNode.innerHTML = `<p class="chat-admin-empty">No messages in this thread yet.</p>`;
      return;
    }
    messages.forEach((message) => {
      renderMessageBubble(message, true);
      if (message.id > lastMessageId) {
        lastMessageId = message.id;
      }
    });
    messagesNode.scrollTop = messagesNode.scrollHeight;
  }

  async function loadThreads() {
    const query = searchInput.value.trim();
    const separator = threadsUrl.includes("?") ? "&" : "?";
    const url = query ? `${threadsUrl}${separator}q=${encodeURIComponent(query)}` : threadsUrl;
    const payload = await requestJson(url, { method: "GET" });
    renderThreadList(payload.threads || []);
  }

  async function openThread(threadId) {
    activeThreadId = threadId;
    lastMessageId = 0;
    await loadThreads();
    const payload = await requestJson(buildMessagesUrl(threadId, 0), { method: "GET" });
    const thread = payload.thread || {};
    headerNode.innerHTML = `
      <h3>${escapeHtml(thread.display_name || "Conversation")}</h3>
      <p>${thread.is_authenticated_user ? "Logged in customer" : "Anonymous visitor"}${thread.is_closed ? " · Closed" : " · Open"}</p>
    `;
    renderMessages(payload.messages || [], true);
    await loadThreads();
    input.focus();
  }

  async function pollActiveThread() {
    if (!activeThreadId) {
      await loadThreads();
      return;
    }
    const payload = await requestJson(buildMessagesUrl(activeThreadId, lastMessageId), { method: "GET" });
    if (payload.messages && payload.messages.length) {
      renderMessages(payload.messages, false);
    }
    await loadThreads();
  }

  async function sendReply(event) {
    event.preventDefault();
    if (!activeThreadId) {
      return;
    }

    const text = input.value.trim();
    if (!text) {
      return;
    }

    form.querySelector("button").disabled = true;
    input.disabled = true;
    try {
      const payload = await requestJson(buildSendUrl(activeThreadId), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ message: text }),
      });
      input.value = "";
      if (payload.message) {
        renderMessages([payload.message], false);
      }
      await loadThreads();
    } finally {
      form.querySelector("button").disabled = false;
      input.disabled = false;
      input.focus();
    }
  }

  searchInput.addEventListener("input", () => {
    if (searchDebounce) {
      window.clearTimeout(searchDebounce);
    }
    searchDebounce = window.setTimeout(() => {
      loadThreads().catch(() => null);
    }, 260);
  });

  form.addEventListener("submit", (event) => {
    sendReply(event).catch(() => null);
  });

  loadThreads().catch(() => null);
  pollTimer = window.setInterval(() => {
    pollActiveThread().catch(() => null);
  }, 2500);

  window.addEventListener("beforeunload", () => {
    if (pollTimer) {
      window.clearInterval(pollTimer);
    }
  });
})();
