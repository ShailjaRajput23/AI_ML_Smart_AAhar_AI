(() => {
  const body = document.body;
  if (!body) return;

  const isAuthenticated = body.dataset.authenticated === "true";
  if (!isAuthenticated) return;

  const timeoutMinutes = Number(body.dataset.sessionTimeoutMinutes || "10");
  const timeoutMs = Math.max(timeoutMinutes, 1) * 60 * 1000;
  const pingIntervalMs = 60 * 1000;
  let timeoutHandle = null;
  let lastPingAt = 0;

  const pingServer = async () => {
    try {
      const response = await fetch("/session/ping", {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });
      if (response.status === 401) {
        window.location.href = "/login";
      }
    } catch (_error) {
      // Ignore transient network/pause failures.
    }
  };

  const resetTimer = () => {
    if (timeoutHandle) {
      clearTimeout(timeoutHandle);
    }
    timeoutHandle = setTimeout(() => {
      window.location.href = "/logout";
    }, timeoutMs);

    const now = Date.now();
    if (now - lastPingAt >= pingIntervalMs) {
      lastPingAt = now;
      pingServer();
    }
  };

  ["mousemove", "mousedown", "keydown", "scroll", "touchstart", "click"].forEach((eventName) => {
    window.addEventListener(eventName, resetTimer, { passive: true });
  });

  resetTimer();
})();
