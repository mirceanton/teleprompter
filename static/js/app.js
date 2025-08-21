/**
 * Remote Teleprompter Application
 * Client-side JavaScript for WebSocket communication and UI control
 */

// Global variables
let ws = null;
let mode = null;
let channel = null;
let isScrolling = false;
let scrollPosition = 0;
let scrollSpeed = 5;
let fontSize = 2.5;
let textWidth = 100;
let isMirrored = false;
let animationId = null;

// Initialize on page load
window.addEventListener("DOMContentLoaded", function () {
  // Generate random channel name
  const randomChannel = "room-" + Math.random().toString(36).substring(2, 8);
  document.getElementById("channelName").value = randomChannel;

  // Set up event listeners
  setupEventListeners();
});

/**
 * Set up all event listeners
 */
function setupEventListeners() {
  // Auto-sync text with debounce
  const scriptEditor = document.getElementById("scriptEditor");
  let syncTimeout;

  scriptEditor.addEventListener("input", function () {
    clearTimeout(syncTimeout);
    syncTimeout = setTimeout(syncText, 300);
  });

  // Handle Enter key in channel input
  document
    .getElementById("channelName")
    .addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        connect();
      }
    });
}

/**
 * Set the application mode (controller or teleprompter)
 */
function setMode(selectedMode) {
  mode = selectedMode;

  // Update button states
  document.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.classList.remove("active");
  });
  event.target.classList.add("active");

  // Update UI if connected
  if (ws && ws.readyState === WebSocket.OPEN) {
    updateUI();
  }
}

/**
 * Connect to WebSocket server
 */
function connect() {
  const channelName = document.getElementById("channelName").value.trim();

  // Validation
  if (!channelName) {
    showNotification("Please enter a channel name", "error");
    return;
  }

  if (!mode) {
    showNotification("Please select a mode first", "error");
    return;
  }

  channel = channelName;

  // Close existing connection
  if (ws) {
    ws.close();
  }

  // Update status
  const status = document.getElementById("status");
  status.className = "status connecting";
  status.textContent = "Connecting...";

  // Create WebSocket connection
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/${channel}`;

  try {
    ws = new WebSocket(wsUrl);
    setupWebSocketHandlers();
  } catch (error) {
    console.error("WebSocket connection error:", error);
    status.className = "status disconnected";
    status.textContent = "Connection failed";
  }
}

/**
 * Set up WebSocket event handlers
 */
function setupWebSocketHandlers() {
  const status = document.getElementById("status");

  ws.onopen = function () {
    console.log("WebSocket connected");
    status.className = "status connected";
    status.textContent = `Connected - ${mode.toUpperCase()} Mode`;
    updateUI();

    // Send mode information
    sendMessage({ type: "mode", mode: mode });

    // Sync initial text if controller
    if (mode === "controller") {
      setTimeout(() => {
        syncText();
        // Also sync initial display settings
        updateWidth();
        updateMirror();
        updateFontSizeDisplay();
      }, 500);
    }
  };

  ws.onmessage = function (event) {
    try {
      const message = JSON.parse(event.data);
      handleMessage(message);
    } catch (error) {
      console.error("Error parsing message:", error);
    }
  };

  ws.onerror = function (error) {
    console.error("WebSocket error:", error);
    status.className = "status disconnected";
    status.textContent = "Connection error";
  };

  ws.onclose = function () {
    console.log("WebSocket disconnected");
    status.className = "status disconnected";
    status.textContent = "Disconnected";

    // Reset UI
    document.getElementById("controllerPanel").style.display = "none";
    document.getElementById("teleprompterPanel").style.display = "none";
  };
}

/**
 * Update UI based on mode
 */
function updateUI() {
  const controllerPanel = document.getElementById("controllerPanel");
  const teleprompterPanel = document.getElementById("teleprompterPanel");

  if (mode === "controller") {
    controllerPanel.style.display = "block";
    teleprompterPanel.style.display = "none";
  } else if (mode === "teleprompter") {
    controllerPanel.style.display = "none";
    teleprompterPanel.style.display = "block";
  }
}

/**
 * Send message through WebSocket
 */
function sendMessage(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  } else {
    console.warn("WebSocket not connected");
  }
}

/**
 * Handle incoming WebSocket messages
 */
function handleMessage(message) {
  if (mode === "teleprompter") {
    switch (message.type) {
      case "text":
        updateTeleprompterText(message.content);
        break;
      case "start":
        startTeleprompterScrolling();
        break;
      case "pause":
        pauseTeleprompterScrolling();
        break;
      case "reset":
        resetTeleprompterScrolling();
        break;
      case "fastforward":
        fastForwardTeleprompter();
        break;
      case "rewind":
        rewindTeleprompter();
        break;
      case "speed":
        scrollSpeed = message.value;
        break;
      case "width":
        updateTeleprompterWidth(message.value);
        break;
      case "mirror":
        setTeleprompterMirror(message.value);
        break;
      case "fontsize":
        fontSize = message.value;
        document.getElementById("teleprompterText").style.fontSize = fontSize + "em";
        break;
    }
  }
}

// Controller Functions
/**
 * Sync text from editor to teleprompter
 */
function syncText() {
  const text = document.getElementById("scriptEditor").value;
  sendMessage({ type: "text", content: text });
}

/**
 * Start scrolling on teleprompter
 */
function startScrolling() {
  syncText();
  sendMessage({ type: "start" });
}

/**
 * Pause scrolling on teleprompter
 */
function pauseScrolling() {
  sendMessage({ type: "pause" });
}

/**
 * Reset scrolling on teleprompter
 */
function resetScrolling() {
  sendMessage({ type: "reset" });
}

/**
 * Fast forward text on teleprompter
 */
function fastForwardText() {
  sendMessage({ type: "fastforward" });
}

/**
 * Rewind text on teleprompter
 */
function rewindText() {
  sendMessage({ type: "rewind" });
}

/**
 * Update scrolling speed
 */
function updateSpeed() {
  const slider = document.getElementById("speedSlider");
  const value = slider.value;
  document.getElementById("speedValue").textContent = value;
  scrollSpeed = parseInt(value);
  sendMessage({ type: "speed", value: scrollSpeed });
}

/**
 * Update text width
 */
function updateWidth() {
  const slider = document.getElementById("widthSlider");
  const value = slider.value;
  document.getElementById("widthValue").textContent = value + "%";
  textWidth = parseInt(value);
  sendMessage({ type: "width", value: textWidth });
}

/**
 * Update mirror setting
 */
function updateMirror() {
  const toggle = document.getElementById("mirrorToggle");
  isMirrored = toggle.checked;
  sendMessage({ type: "mirror", value: isMirrored });
}

/**
 * Increase font size from controller
 */
function increaseFontSize() {
  fontSize = Math.max(1, Math.min(5, fontSize + 0.2));
  updateFontSizeDisplay();
  sendMessage({ type: "fontsize", value: fontSize });
}

/**
 * Decrease font size from controller
 */
function decreaseFontSize() {
  fontSize = Math.max(1, Math.min(5, fontSize - 0.2));
  updateFontSizeDisplay();
  sendMessage({ type: "fontsize", value: fontSize });
}

/**
 * Update font size display in controller
 */
function updateFontSizeDisplay() {
  const fontSizeValue = document.getElementById("fontSizeValue");
  if (fontSizeValue) {
    fontSizeValue.textContent = fontSize.toFixed(1) + "em";
  }
}

// Teleprompter Functions
/**
 * Update teleprompter text content
 */
function updateTeleprompterText(text) {
  document.getElementById("teleprompterContent").textContent = text;
}

/**
 * Update teleprompter text width
 */
function updateTeleprompterWidth(width) {
  textWidth = width;
  const content = document.getElementById("teleprompterContent");
  content.style.maxWidth = width + "%";
}

/**
 * Set teleprompter mirror mode
 */
function setTeleprompterMirror(mirror) {
  isMirrored = mirror;
  const teleprompterText = document.getElementById("teleprompterText");
  const mirrorIndicator = document.getElementById("mirrorIndicator");

  if (mirror) {
    teleprompterText.classList.add("mirrored");
    if (mirrorIndicator) mirrorIndicator.style.display = "block";
  } else {
    teleprompterText.classList.remove("mirrored");
    if (mirrorIndicator) mirrorIndicator.style.display = "none";
  }
}

/**
 * Toggle mirror mode (for direct control on teleprompter)
 */
function toggleMirror() {
  isMirrored = !isMirrored;
  setTeleprompterMirror(isMirrored);
  // Send update to controller
  sendMessage({ type: "mirror", value: isMirrored });
}

/**
 * Change text width (for direct control on teleprompter)
 */
function changeWidth(delta) {
  textWidth = Math.max(30, Math.min(100, textWidth + delta));
  updateTeleprompterWidth(textWidth);
  // Send update to controller
  sendMessage({ type: "width", value: textWidth });
}

/**
 * Start teleprompter scrolling animation
 */
function startTeleprompterScrolling() {
  isScrolling = true;
  animateTeleprompter();
}

/**
 * Pause teleprompter scrolling
 */
function pauseTeleprompterScrolling() {
  isScrolling = false;
  if (animationId) {
    cancelAnimationFrame(animationId);
  }
}

/**
 * Reset teleprompter to beginning
 */
function resetTeleprompterScrolling() {
  scrollPosition = 0;
  const content = document.getElementById("teleprompterContent");
  content.style.transform = `translateX(-50%) translateY(${scrollPosition}px)`;
  pauseTeleprompterScrolling();
}

/**
 * Fast forward teleprompter text
 */
function fastForwardTeleprompter() {
  const content = document.getElementById("teleprompterContent");
  const container = document.getElementById("teleprompterText");
  
  // Move forward by a large amount
  scrollPosition -= scrollSpeed * 5;
  
  // Check boundaries - don't go past the end
  const maxScroll = -(content.offsetHeight - container.offsetHeight + 100);
  if (scrollPosition < maxScroll) {
    scrollPosition = maxScroll;
  }
  
  // Apply transform
  content.style.transform = `translateX(-50%) translateY(${scrollPosition}px)`;
}

/**
 * Rewind teleprompter text
 */
function rewindTeleprompter() {
  const content = document.getElementById("teleprompterContent");
  
  // Move backward by a large amount
  scrollPosition += scrollSpeed * 5;
  
  // Check boundaries - don't go past the beginning
  if (scrollPosition > 0) {
    scrollPosition = 0;
  }
  
  // Apply transform
  content.style.transform = `translateX(-50%) translateY(${scrollPosition}px)`;
}

/**
 * Animate teleprompter scrolling
 */
function animateTeleprompter() {
  if (!isScrolling) return;

  const content = document.getElementById("teleprompterContent");
  const container = document.getElementById("teleprompterText");

  // Update scroll position
  scrollPosition -= scrollSpeed / 10;

  // Check boundaries
  const maxScroll = -(content.offsetHeight - container.offsetHeight + 100);
  if (scrollPosition < maxScroll) {
    scrollPosition = maxScroll;
    isScrolling = false;
  }

  // Apply transform (maintaining center alignment)
  content.style.transform = `translateX(-50%) translateY(${scrollPosition}px)`;

  // Continue animation
  if (isScrolling) {
    animationId = requestAnimationFrame(animateTeleprompter);
  }
}

/**
 * Exit teleprompter view
 */
function exitTeleprompter() {
  document.getElementById("teleprompterPanel").style.display = "none";
  pauseTeleprompterScrolling();
}

/**
 * Change teleprompter font size
 */
function changeFontSize(delta) {
  fontSize = Math.max(1, Math.min(5, fontSize + delta));
  document.getElementById("teleprompterText").style.fontSize = fontSize + "em";
}

/**
 * Show notification (optional enhancement)
 */
function showNotification(message, type = "info") {
  // Simple alert for now, can be replaced with better notification system
  alert(message);
}

// Keyboard shortcuts (optional enhancement)
document.addEventListener("keydown", function (e) {
  // Only work in teleprompter mode
  if (
    mode === "teleprompter" &&
    document.getElementById("teleprompterPanel").style.display === "block"
  ) {
    switch (e.key) {
      case " ": // Spacebar
        e.preventDefault();
        if (isScrolling) {
          pauseTeleprompterScrolling();
        } else {
          startTeleprompterScrolling();
        }
        break;
      case "Escape":
        exitTeleprompter();
        break;
      case "r":
      case "R":
        resetTeleprompterScrolling();
        break;
      case "+":
      case "=":
        changeFontSize(0.2);
        break;
      case "-":
      case "_":
        changeFontSize(-0.2);
        break;
      case "m":
      case "M":
        toggleMirror();
        break;
      case "ArrowLeft":
        e.preventDefault();
        changeWidth(-10);
        break;
      case "ArrowRight":
        e.preventDefault();
        changeWidth(10);
        break;
    }
  }
});
