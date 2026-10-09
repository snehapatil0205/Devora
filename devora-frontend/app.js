(() => {
  let API = (window.DEVORA_API_BASE || "http://localhost:8001").replace(/\/$/, "");
  const $ = (id) => document.getElementById(id);

  let toastTimer;

  const toast = (message) => {
    const el = $("toast");
    if (!el) return;
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
  };

  async function request(path, options = {}) {
    const response = await fetch(API + path, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
    });

    const raw = await response.text();
    let data;
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      data = { detail: raw };
    }

    if (!response.ok) {
      throw new Error(
        data.detail || data.message || `Request failed (${response.status})`
      );
    }

    return data;
  }

  // =========================================
  // BACKEND AUTO-DETECTION & HEALTH
  // =========================================

  async function detectBackend() {
    const candidates = [
      API,
      "http://localhost:8001",
      "http://127.0.0.1:8001",
      "http://localhost:8000",
      "http://127.0.0.1:8000",
    ];

    for (const url of candidates) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 1200);
        const res = await fetch(`${url}/health`, { signal: controller.signal });
        clearTimeout(timeout);
        if (res.ok) {
          API = url;
          updatePreviewLinks();
          return true;
        }
      } catch {}
    }
    return false;
  }

  function updatePreviewLinks() {
    const previewUrl = `${API}/api/workspace/preview`;
    if ($("navPreviewLink")) $("navPreviewLink").href = previewUrl;
  }

  async function health() {
    const dot = $("connectionDot");
    const title = $("connectionTitle");
    const text = $("connectionText");

    if (!dot || !title || !text) return;

    const isHealthy = await detectBackend();

    if (isHealthy) {
      dot.className = "status-dot online";
      title.textContent = "Backend connected";
      text.textContent = `${API.replace(/^https?:\/\//, "")} · ready`;
    } else {
      dot.className = "status-dot offline";
      title.textContent = "Backend offline";
      text.textContent = "Start FastAPI on port 8001";
    }
  }

  $("retryHealth")?.addEventListener("click", health);
  health();
  setInterval(health, 15000);

  // =========================================
  // CHAT INTERFACE & LIVE PREVIEW IN CHAT
  // =========================================

  const chatFeed = $("chatFeed");
  const welcomeHeader = $("welcomeHeader");
  const input = $("taskInput");
  const runBtn = $("runBtn");

  let recent = [];
  let messageCounter = 0;

  function getTimeString() {
    return new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function addRecent(query) {
    if (!query) return;
    recent = [query, ...recent.filter((q) => q !== query)].slice(0, 5);

    const list = $("recentList");
    if (!list) return;

    list.innerHTML = "";
    recent.forEach((q) => {
      const button = document.createElement("button");
      button.className = "recent-task";
      button.textContent = q;
      button.title = q;

      button.addEventListener("click", () => {
        if (input) {
          input.value = q;
          input.focus();
        }
      });

      list.appendChild(button);
    });
  }

  function setBusy(busy) {
    if (!runBtn) return;
    runBtn.disabled = busy;

    const label = runBtn.querySelector(".run-label");
    const arrow = runBtn.querySelector(".run-arrow");

    if (label) label.textContent = busy ? "Building…" : "Send";
    if (arrow) {
      arrow.innerHTML = busy ? '<span class="spinner"></span>' : "↑";
    }
  }

  function scrollChatToBottom() {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth",
    });
  }

  // 1. Append User Message
  function appendUserMessage(text) {
    welcomeHeader?.classList.add("hidden");

    const msgEl = document.createElement("div");
    msgEl.className = "chat-msg user-msg";

    msgEl.innerHTML = `
      <div class="msg-avatar user-avatar">U</div>
      <div class="msg-body">
        <div class="msg-meta">
          <strong>You</strong>
          <span>${getTimeString()}</span>
        </div>
        <div class="msg-text">${escapeHtml(text)}</div>
      </div>
    `;

    chatFeed.appendChild(msgEl);
    scrollChatToBottom();
  }

  // 2. Append Thinking Indicator
  function appendThinkingMessage() {
    const thinkingEl = document.createElement("div");
    thinkingEl.id = "thinkingMsg";
    thinkingEl.className = "chat-msg assistant-msg thinking-msg";

    thinkingEl.innerHTML = `
      <div class="msg-avatar devora-avatar">D<span>✦</span></div>
      <div class="msg-body">
        <div class="msg-meta">
          <strong>Devora Agent</strong>
          <span>Working…</span>
        </div>
        <div class="thinking-box">
          <span class="spinner"></span>
          <span>Designing and building your application code…</span>
        </div>
      </div>
    `;

    chatFeed.appendChild(thinkingEl);
    scrollChatToBottom();
  }

  function removeThinkingMessage() {
    $("thinkingMsg")?.remove();
  }

  // 3. Append Assistant Message With Embedded Live Preview
  function appendAssistantMessage({ text, toolCalls = [], files = [] }) {
    removeThinkingMessage();

    messageCounter++;
    const cardId = `previewCard_${messageCounter}`;
    const frameId = `frame_${messageCounter}`;

    const msgEl = document.createElement("div");
    msgEl.className = "chat-msg assistant-msg";

    // Format tool pills
    let toolsHtml = "";
    if (toolCalls.length) {
      toolsHtml = `
        <div class="tool-chips-row">
          <span class="tool-chips-label">EXECUTED TOOLS:</span>
          ${toolCalls
            .map(
              (tc) =>
                `<span class="tool-chip"><code>${escapeHtml(tc.tool || "tool")}</code></span>`
            )
            .join("")}
        </div>
      `;
    }

    const previewUrl = `${API}/api/workspace/preview?t=${Date.now()}`;

    msgEl.innerHTML = `
      <div class="msg-avatar devora-avatar">D<span>✦</span></div>
      <div class="msg-body">
        <div class="msg-meta">
          <strong>Devora Agent</strong>
          <span class="status-pill">Ready</span>
          <span>${getTimeString()}</span>
        </div>

        <div class="msg-text">${formatMarkdownText(text)}</div>

        ${toolsHtml}

        <!-- LIVE APPLICATION CARD EMBEDDED DIRECTLY IN CHAT -->
        <div class="chat-app-card" id="${cardId}">
          <div class="chat-app-header">
            <div class="app-info">
              <span class="app-icon">◈</span>
              <div>
                <strong>Live Application Preview</strong>
                <small>Generated in workspace/index.html</small>
              </div>
            </div>

            <div class="chat-app-controls">
              <div class="mode-toggles">
                <button class="mode-btn active" data-mode="desktop" title="Desktop view">💻 Desktop</button>
                <button class="mode-btn" data-mode="mobile" title="Mobile view">📱 Mobile</button>
              </div>
              <button class="action-btn reload-btn" title="Reload application">↻</button>
              <a class="action-btn newtab-btn" href="${previewUrl}" target="_blank" title="Open full screen in a new tab">↗ New Tab</a>
            </div>
          </div>

          <div class="chat-app-frame-wrap desktop-mode">
            <iframe
              id="${frameId}"
              src="${previewUrl}"
              title="Application Preview"
              sandbox="allow-scripts allow-forms allow-same-origin allow-modals allow-popups"
              referrerpolicy="no-referrer"
            ></iframe>
          </div>
        </div>
      </div>
    `;

    chatFeed.appendChild(msgEl);

    // Setup controls for this preview card
    const card = $(cardId);
    if (card) {
      const frameWrap = card.querySelector(".chat-app-frame-wrap");
      const iframe = card.querySelector("iframe");
      const desktopBtn = card.querySelector('[data-mode="desktop"]');
      const mobileBtn = card.querySelector('[data-mode="mobile"]');
      const reloadBtn = card.querySelector(".reload-btn");

      desktopBtn?.addEventListener("click", () => {
        desktopBtn.classList.add("active");
        mobileBtn?.classList.remove("active");
        frameWrap.className = "chat-app-frame-wrap desktop-mode";
      });

      mobileBtn?.addEventListener("click", () => {
        mobileBtn.classList.add("active");
        desktopBtn?.classList.remove("active");
        frameWrap.className = "chat-app-frame-wrap mobile-mode";
      });

      reloadBtn?.addEventListener("click", () => {
        if (iframe) {
          iframe.src = `${API}/api/workspace/preview?t=${Date.now()}`;
          toast("Preview reloaded.");
        }
      });
    }

    scrollChatToBottom();
  }

  // 4. Run Task & Stream to Chat
  async function sendMessage(userQuery) {
    const query = (userQuery || input?.value || "").trim();

    if (!query) {
      toast("Please type what application to build.");
      input?.focus();
      return;
    }

    if (input) input.value = "";
    addRecent(query);
    appendUserMessage(query);
    appendThinkingMessage();
    setBusy(true);

    try {
      const data = await request("/api/agent/run", {
        method: "POST",
        body: JSON.stringify({ query }),
      });

      appendAssistantMessage({
        text: data.response || "Your application is ready! Test it below.",
        toolCalls: Array.isArray(data.tool_calls) ? data.tool_calls : [],
        files: Array.isArray(data.files) ? data.files : [],
      });

      toast("Application created and live in chat!");
    } catch (error) {
      removeThinkingMessage();

      const errorMsg = document.createElement("div");
      errorMsg.className = "chat-msg assistant-msg";
      errorMsg.innerHTML = `
        <div class="msg-avatar devora-avatar">D<span>✦</span></div>
        <div class="msg-body">
          <div class="msg-meta">
            <strong>Devora Agent</strong>
            <span class="status-pill error">Failed</span>
            <span>${getTimeString()}</span>
          </div>
          <div class="msg-text error-text">
            <strong>Could not complete request:</strong><br />
            ${escapeHtml(error.message)}<br /><br />
            Make sure the backend is running at <code>${API}</code>.
          </div>
        </div>
      `;
      chatFeed.appendChild(errorMsg);
      scrollChatToBottom();
      toast("Error: " + error.message);
    } finally {
      setBusy(false);
    }
  }

  runBtn?.addEventListener("click", () => sendMessage());

  input?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  // New Chat button
  $("newTaskBtn")?.addEventListener("click", () => {
    chatFeed.innerHTML = "";
    welcomeHeader?.classList.remove("hidden");
    if (input) {
      input.value = "";
      input.focus();
    }
    toast("Started new chat.");
  });

  // Clear workspace
  $("clearWorkspaceBtn")?.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to clear all workspace files?")) return;
    try {
      await request("/api/workspace/clear", { method: "POST" });
      toast("Workspace cleared.");
      // Reload any active preview in chat
      document.querySelectorAll(".chat-app-frame-wrap iframe").forEach((f) => {
        f.src = `${API}/api/workspace/preview?t=${Date.now()}`;
      });
    } catch (err) {
      toast("Could not clear workspace: " + err.message);
    }
  });

  // Navigation & Modals
  $("helpBtn")?.addEventListener("click", () => $("helpModal")?.classList.remove("hidden"));
  $("closeHelp")?.addEventListener("click", () => $("helpModal")?.classList.add("hidden"));
  $("helpModal")?.addEventListener("click", (e) => {
    if (e.target.id === "helpModal") $("helpModal").classList.add("hidden");
  });
  $("mobileMenu")?.addEventListener("click", () => $("sidebar")?.classList.toggle("open"));

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      chatFeed.innerHTML = "";
      welcomeHeader?.classList.remove("hidden");
      input?.focus();
    }
    if (event.key === "Escape") {
      $("helpModal")?.classList.add("hidden");
      $("sidebar")?.classList.remove("open");
    }
  });

  // Utilities
  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatMarkdownText(text) {
    if (!text) return "";
    let safe = escapeHtml(text);
    // Bold
    safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Code blocks
    safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Newlines
    safe = safe.replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br />");
    return `<p>${safe}</p>`;
  }

  // =========================================
  // WORKSPACE FILE EXPLORER (for workspace.html)
  // =========================================

  const tree = $("fileTree");
  if (tree) {
    const fileContents = new Map();

    const iconFor = (path, type) =>
      type === "directory"
        ? "▸"
        : /\.(html|htm)$/i.test(path)
          ? "◈"
          : /\.(css|scss)$/i.test(path)
            ? "🎨"
            : /\.(js|jsx|ts|tsx)$/i.test(path)
              ? "⚡"
              : /\.py$/i.test(path)
                ? "🐍"
                : "▤";

    async function loadFiles() {
      tree.innerHTML =
        '<div class="tree-loading"><span class="spinner"></span> Loading workspace files…</div>';

      try {
        const data = await request("/api/workspace/files");
        const items = Array.isArray(data.items) ? data.items : [];

        if ($("workspacePath")) $("workspacePath").textContent = data.workspace || "Workspace root";
        if ($("fileCount")) {
          $("fileCount").textContent = `${items.filter((i) => i.type === "file").length} files`;
        }

        tree.innerHTML = "";

        if (!items.length) {
          tree.innerHTML =
            '<div class="tree-loading">No files in workspace yet. Ask Devora to build an app!</div>';
          return;
        }

        const rootNode = { name: "root", children: [] };
        const sorted = items.slice().sort((a, b) => a.path.localeCompare(b.path));

        sorted.forEach((item) => {
          const parts = item.path.split("/").filter(Boolean);
          let node = rootNode;

          parts.forEach((part, index) => {
            node.children ||= [];
            let child = node.children.find((entry) => entry.name === part);
            const isDir = index < parts.length - 1 || item.type === "directory";

            if (!child) {
              child = {
                name: part,
                path: parts.slice(0, index + 1).join("/"),
                type: isDir ? "directory" : "file",
                children: [],
              };
              node.children.push(child);
            }
            if (index === parts.length - 1 && item.type === "file") {
              child.type = "file";
            }
            node = child;
          });
        });

        function render(nodes, parent, depth = 0) {
          nodes.sort((a, b) =>
            a.type === b.type
              ? a.name.localeCompare(b.name)
              : a.type === "directory" ? -1 : 1
          );

          nodes.forEach((node) => {
            const row = document.createElement("div");
            row.className = "tree-row";
            row.style.paddingLeft = `${8 + depth * 12}px`;

            const icon = document.createElement("span");
            icon.className = "tree-icon";
            icon.textContent = iconFor(node.path, node.type);

            const name = document.createElement("span");
            name.className = "tree-name";
            name.textContent = node.name;

            row.append(icon, name);

            if (node.type === "directory") {
              const kind = document.createElement("span");
              kind.className = "tree-kind";
              kind.textContent = "DIR";
              row.appendChild(kind);

              let children;
              row.addEventListener("click", () => {
                if (children) {
                  children.classList.toggle("hidden");
                  icon.textContent = children.classList.contains("hidden") ? "▸" : "▾";
                }
              });

              parent.appendChild(row);

              if (node.children.length) {
                children = document.createElement("div");
                children.className = "tree-children";
                parent.appendChild(children);
                render(node.children, children, depth + 1);
              }
            } else {
              row.title = node.path;
              row.addEventListener("click", () => openFile(node.path, row));
              parent.appendChild(row);
            }
          });
        }

        render(rootNode.children, tree);
      } catch (error) {
        tree.innerHTML = `<div class="tree-error">${error.message}. Start backend on port 8001.</div>`;
      }
    }

    async function openFile(path, row) {
      tree.querySelectorAll(".tree-row.selected").forEach((el) => el.classList.remove("selected"));
      row.classList.add("selected");

      $("editorFilename").textContent = path;
      $("editorStatus").textContent = "Loading…";
      $("editorMeta").textContent = "Fetching file";
      $("editorBody").innerHTML =
        '<div class="empty-editor"><span class="spinner"></span><p>Reading file…</p></div>';

      $("copyFile").disabled = true;

      try {
        let content = fileContents.get(path);
        if (content === undefined) {
          const data = await request("/api/workspace/read?path=" + encodeURIComponent(path));
          content = data.content ?? "";
          fileContents.set(path, content);
        }

        const pre = document.createElement("pre");
        pre.textContent = content;

        $("editorBody").innerHTML = "";
        $("editorBody").appendChild(pre);

        $("editorStatus").textContent = "Read only preview";
        $("editorMeta").textContent =
          `${content.split("\n").length} lines · ${(new Blob([content]).size / 1024).toFixed(1)} KB`;

        $("copyFile").disabled = false;
        $("copyFile").onclick = async () => {
          try {
            await navigator.clipboard.writeText(content);
            toast("File contents copied.");
          } catch {
            toast("Clipboard access unavailable.");
          }
        };
      } catch (error) {
        $("editorBody").textContent = error.message;
        $("editorStatus").textContent = "Error";
      }
    }

    $("refreshFiles")?.addEventListener("click", loadFiles);
    loadFiles();
  }
})();