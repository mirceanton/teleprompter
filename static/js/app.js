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
let isHorizontalMirrored = false;
let isVerticalMirrored = false;
let mirrorMode = "none"; // "none", "horizontal", "vertical", "both" - kept for backward compatibility
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
        updateWidthDisplay();
        updateMirrorFromState();
        updateFontSizeDisplay();
      }, 500);
    }
    
    // Request connection info update
    setTimeout(() => {
      sendMessage({ type: "request_connection_info" });
    }, 1000);
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
        setTeleprompterMirror(message.value, message.horizontal, message.vertical);
        break;
      case "fontsize":
        fontSize = message.value;
        document.getElementById("teleprompterText").style.fontSize = fontSize + "em";
        break;
      case "connection_update":
        updateConnectionInfo(message.connection_count);
        break;
    }
  } else if (mode === "controller") {
    // Handle messages that update controller UI
    switch (message.type) {
      case "mirror":
        // Update controller toggles when teleprompter changes mirror mode
        setMirrorState(message.horizontal, message.vertical);
        break;
      case "width":
        // Update controller width slider when teleprompter changes width
        textWidth = message.value;
        const widthSlider = document.getElementById("widthSlider");
        const widthValue = document.getElementById("widthValue");
        if (widthSlider) widthSlider.value = textWidth;
        if (widthValue) widthValue.textContent = textWidth + "%";
        break;
      case "connection_update":
        updateConnectionInfo(message.connection_count);
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
 * Update text width display
 */
function updateWidthDisplay() {
  const widthValue = document.getElementById("widthValue");
  if (widthValue) {
    widthValue.textContent = textWidth + "%";
  }
}

/**
 * Increase text width from controller
 */
function increaseWidth() {
  textWidth = Math.max(30, Math.min(100, textWidth + 5));
  updateWidthDisplay();
  sendMessage({ type: "width", value: textWidth });
}

/**
 * Decrease text width from controller
 */
function decreaseWidth() {
  textWidth = Math.max(30, Math.min(100, textWidth - 5));
  updateWidthDisplay();
  sendMessage({ type: "width", value: textWidth });
}

/**
 * Update horizontal mirror setting
 */
function updateHorizontalMirror() {
  const checkbox = document.getElementById("horizontalMirror");
  isHorizontalMirrored = checkbox.checked;
  updateMirrorFromState();
}

/**
 * Update vertical mirror setting
 */
function updateVerticalMirror() {
  const checkbox = document.getElementById("verticalMirror");
  isVerticalMirrored = checkbox.checked;
  updateMirrorFromState();
}

/**
 * Update mirror mode based on current state and send to teleprompter
 */
function updateMirrorFromState() {
  // Determine mirror mode from boolean states
  if (isHorizontalMirrored && isVerticalMirrored) {
    mirrorMode = "both";
  } else if (isHorizontalMirrored) {
    mirrorMode = "horizontal";
  } else if (isVerticalMirrored) {
    mirrorMode = "vertical";
  } else {
    mirrorMode = "none";
  }
  
  isMirrored = mirrorMode !== "none"; // For backward compatibility
  sendMessage({ 
    type: "mirror", 
    value: mirrorMode,
    horizontal: isHorizontalMirrored,
    vertical: isVerticalMirrored
  });
}

/**
 * Set mirror state from incoming message
 */
function setMirrorState(horizontal, vertical) {
  isHorizontalMirrored = horizontal;
  isVerticalMirrored = vertical;
  
  // Update UI toggles
  const horizontalCheckbox = document.getElementById("horizontalMirror");
  const verticalCheckbox = document.getElementById("verticalMirror");
  
  if (horizontalCheckbox) horizontalCheckbox.checked = isHorizontalMirrored;
  if (verticalCheckbox) verticalCheckbox.checked = isVerticalMirrored;
  
  // Update mirror mode for backward compatibility
  if (isHorizontalMirrored && isVerticalMirrored) {
    mirrorMode = "both";
  } else if (isHorizontalMirrored) {
    mirrorMode = "horizontal";
  } else if (isVerticalMirrored) {
    mirrorMode = "vertical";
  } else {
    mirrorMode = "none";
  }
  
  isMirrored = mirrorMode !== "none";
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
function setTeleprompterMirror(mode, horizontal, vertical) {
  mirrorMode = mode;
  
  // Update boolean states if provided
  if (horizontal !== undefined) isHorizontalMirrored = horizontal;
  if (vertical !== undefined) isVerticalMirrored = vertical;
  
  // Keep isMirrored for backward compatibility
  isMirrored = mode !== "none";
  
  const teleprompterText = document.getElementById("teleprompterText");
  const mirrorIndicator = document.getElementById("mirrorIndicator");

  // Remove all mirror classes
  teleprompterText.classList.remove("mirrored-horizontal", "mirrored-vertical", "mirrored-both");
  
  // Add appropriate mirror class based on mode
  if (mode === "horizontal") {
    teleprompterText.classList.add("mirrored-horizontal");
    if (mirrorIndicator) {
      mirrorIndicator.textContent = "HORIZONTAL MIRROR";
      mirrorIndicator.style.display = "block";
    }
  } else if (mode === "vertical") {
    teleprompterText.classList.add("mirrored-vertical");
    if (mirrorIndicator) {
      mirrorIndicator.textContent = "VERTICAL MIRROR";
      mirrorIndicator.style.display = "block";
    }
  } else if (mode === "both") {
    teleprompterText.classList.add("mirrored-both");
    if (mirrorIndicator) {
      mirrorIndicator.textContent = "BOTH MIRRORS";
      mirrorIndicator.style.display = "block";
    }
  } else {
    // mode === "none"
    if (mirrorIndicator) mirrorIndicator.style.display = "none";
  }
}

/**
 * Toggle mirror mode (for direct control on teleprompter)
 */
function toggleMirror() {
  // Cycle through mirror modes: none -> horizontal -> vertical -> both -> none
  const modes = ["none", "horizontal", "vertical", "both"];
  const currentIndex = modes.indexOf(mirrorMode);
  const nextIndex = (currentIndex + 1) % modes.length;
  mirrorMode = modes[nextIndex];
  
  // Update boolean states based on new mode
  isHorizontalMirrored = mirrorMode === "horizontal" || mirrorMode === "both";
  isVerticalMirrored = mirrorMode === "vertical" || mirrorMode === "both";
  
  setTeleprompterMirror(mirrorMode, isHorizontalMirrored, isVerticalMirrored);
  // Send update to controller
  sendMessage({ 
    type: "mirror", 
    value: mirrorMode,
    horizontal: isHorizontalMirrored,
    vertical: isVerticalMirrored
  });
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

/**
 * Update connection information display
 */
function updateConnectionInfo(connectionCount) {
  const connectionInfo = document.getElementById("connectionInfo");
  const connectionCountElement = document.getElementById("connectionCount");
  const multiTeleprompterNote = document.getElementById("multiTeleprompterNote");
  
  if (connectionInfo && connectionCountElement) {
    connectionCountElement.textContent = connectionCount;
    connectionInfo.style.display = "block";
    
    // Show multi-teleprompter note if more than one connection
    if (multiTeleprompterNote) {
      if (connectionCount > 1) {
        multiTeleprompterNote.style.display = "block";
      } else {
        multiTeleprompterNote.style.display = "none";
      }
    }
  }
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
