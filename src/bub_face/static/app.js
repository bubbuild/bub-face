const stage = document.getElementById("stage");
const clockPanel = document.getElementById("clockPanel");
const clockTime = document.getElementById("clockTime");
const clockDate = document.getElementById("clockDate");
const clockLunar = document.getElementById("clockLunar");
const eyeElements = Array.from(document.querySelectorAll(".eye"));
const eyeCores = eyeElements.map((eye) => eye.querySelector(".eye-core"));
const CONTENT_SCALE = 1.5;

const state = {
  data: null,
  displayMode: "face",
  blinkTimer: null,
  clockTimer: null,
  socket: null,
};

async function boot() {
  const response = await fetch("/api/state");
  const payload = await response.json();

  applySnapshot(payload);
  connectSocket();
}

function applySnapshot(snapshot) {
  state.displayMode = snapshot.display_mode ?? "face";
  applyState(snapshot.state);
}

function applyState(nextState) {
  state.data = nextState;

  document.documentElement.style.setProperty("--bg", nextState.background);
  document.documentElement.style.setProperty("--accent", nextState.accent);
  document.documentElement.style.setProperty("--spark", nextState.spark);
  document.documentElement.style.setProperty("--content-scale", String(CONTENT_SCALE));
  syncDisplayMode();

  const sizePreset = getEmotionPreset(nextState.emotion);
  const eyeWidth = `${Math.round((sizePreset.width + (1 - nextState.pupil_size) * 38) * CONTENT_SCALE)}px`;
  const eyeHeight = `${Math.round((sizePreset.height + nextState.openness * 24) * CONTENT_SCALE)}px`;
  const glowStrength = Math.round(42 + nextState.glow * 90);

  document.documentElement.style.setProperty("--eye-width", `min(33vw, ${eyeWidth})`);
  document.documentElement.style.setProperty("--eye-height", `min(27vw, ${eyeHeight})`);

  eyeElements.forEach((eye, index) => {
    const side = index === 0 ? -1 : 1;
    const offsetX = Math.round(nextState.pupil_x * 26 * CONTENT_SCALE);
    const offsetY = Math.round(nextState.pupil_y * 14 * CONTENT_SCALE);

    eye.style.setProperty("--eye-offset-x", `${offsetX}px`);
    eye.style.setProperty("--eye-offset-y", `${offsetY}px`);
    eye.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
    eyeCores[index].style.clipPath = createEyeClip(nextState, side);
    eyeCores[index].style.borderRadius = createEyeRadius(nextState, side);
    eyeCores[index].style.transform = createEyeTransform(nextState, side);
    eyeCores[index].style.boxShadow = [
      `0 0 18px color-mix(in srgb, ${nextState.accent} 90%, transparent)`,
      `0 0 36px color-mix(in srgb, ${nextState.accent} 78%, transparent)`,
      `0 0 ${glowStrength}px color-mix(in srgb, ${nextState.accent} 58%, transparent)`,
      `0 0 ${glowStrength + 52}px color-mix(in srgb, ${nextState.accent} 34%, transparent)`,
    ].join(", ");
    eyeCores[index].style.opacity = String(0.72 + nextState.glow * 0.28);
  });

  if (state.displayMode === "face") {
    scheduleBlink();
  }
}

function createEyeClip(nextState, side) {
  const preset = getEmotionPreset(nextState.emotion);
  const blinkTop = clamp(Math.round((1 - nextState.openness) * 24), 0, 18);
  const blinkBottom = clamp(Math.round((1 - nextState.openness) * 18), 0, 14);
  const slant = Math.round(nextState.brow_tilt * preset.slant * side);

  return polygonFromPoints([
    [clamp(preset.leftTop - slant, 0, 24), blinkTop + preset.topInset],
    [clamp(preset.rightTop - slant, 76, 100), blinkTop + preset.topInset],
    [100, preset.sideTop],
    [100, preset.sideBottom],
    [clamp(preset.rightBottom + slant, 76, 100), 100 - blinkBottom - preset.bottomInset],
    [clamp(preset.leftBottom + slant, 0, 24), 100 - blinkBottom - preset.bottomInset],
    [0, preset.sideBottom],
    [0, preset.sideTop],
  ]);
}

function createEyeRadius(nextState, side) {
  const preset = getEmotionPreset(nextState.emotion);
  const topOuter = clamp(preset.radiusTopOuter - nextState.brow_tilt * side * 10, 4, 40);
  const topInner = clamp(preset.radiusTopInner + nextState.brow_tilt * side * 12, 8, 54);
  const bottomOuter = clamp(preset.radiusBottomOuter + nextState.eyelid_curve * 10, 8, 42);
  const bottomInner = clamp(preset.radiusBottomInner - nextState.eyelid_curve * 8, 6, 38);

  return `${topOuter}px ${topInner}px ${bottomOuter}px ${bottomInner}px`;
}

function createEyeTransform(nextState, side) {
  const preset = getEmotionPreset(nextState.emotion);
  const openness = clamp(nextState.openness * preset.openScale, 0.12, 1.15);
  const skew = nextState.brow_tilt * side * (6 + preset.slant * 0.3);
  const stretch = preset.widthScale + (1 - nextState.pupil_size) * 0.18;

  return `scaleY(${openness}) scaleX(${stretch}) skewX(${skew}deg)`;
}

function scheduleBlink() {
  window.clearTimeout(state.blinkTimer);
  const delay = (state.data.blink_interval + Math.random() * 1.2) * 1000;
  state.blinkTimer = window.setTimeout(triggerBlink, delay);
}

function triggerBlink() {
  if (state.displayMode !== "face") {
    return;
  }
  eyeCores.forEach((eyeCore) => {
    eyeCore.style.transform = `${eyeCore.style.transform} scaleY(0.08)`;
    eyeCore.style.opacity = "0.55";
  });

  window.setTimeout(() => {
    applyState(state.data);
  }, 120);
}

function connectSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  state.socket = new WebSocket(`${protocol}://${window.location.host}/ws`);
  state.socket.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "state") {
      applySnapshot(payload);
    }
  });
}

function syncDisplayMode() {
  stage.classList.toggle("is-clock", state.displayMode === "clock");
  stage.classList.toggle("is-face", state.displayMode === "face");

  if (state.displayMode === "clock") {
    window.clearTimeout(state.blinkTimer);
    startClock();
    return;
  }

  stopClock();
}

function startClock() {
  if (state.clockTimer !== null) {
    renderClock();
    return;
  }

  renderClock();
  state.clockTimer = window.setInterval(renderClock, 1000);
}

function stopClock() {
  if (state.clockTimer === null) {
    return;
  }

  window.clearInterval(state.clockTimer);
  state.clockTimer = null;
}

function renderClock() {
  const now = new Date();
  clockTime.textContent = new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(now);
  clockDate.textContent = new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  }).format(now);
  const lunarText = formatLunarDate(now);
  clockLunar.textContent = lunarText;
  clockLunar.hidden = lunarText === "";
}

function formatLunarDate(value) {
  try {
    const lunarDate = new Intl.DateTimeFormat("zh-CN-u-ca-chinese-nu-hanidec", {
      year: "numeric",
      month: "long",
      day: "numeric",
    }).format(value);
    return `农历 ${lunarDate}`;
  } catch {
    return "";
  }
}

function getEmotionPreset(emotion) {
  const presets = {
    neutral: {
      width: 138,
      height: 168,
      openScale: 1,
      widthScale: 1,
      slant: 4,
      leftTop: 16,
      rightTop: 84,
      leftBottom: 14,
      rightBottom: 86,
      topInset: 0,
      bottomInset: 0,
      sideTop: 18,
      sideBottom: 82,
      radiusTopOuter: 24,
      radiusTopInner: 24,
      radiusBottomOuter: 22,
      radiusBottomInner: 22,
    },
    happy: {
      width: 144,
      height: 156,
      openScale: 0.92,
      widthScale: 1.08,
      slant: 12,
      leftTop: 12,
      rightTop: 88,
      leftBottom: 10,
      rightBottom: 90,
      topInset: 10,
      bottomInset: 0,
      sideTop: 24,
      sideBottom: 82,
      radiusTopOuter: 34,
      radiusTopInner: 34,
      radiusBottomOuter: 18,
      radiusBottomInner: 18,
    },
    sad: {
      width: 140,
      height: 150,
      openScale: 0.88,
      widthScale: 1,
      slant: -10,
      leftTop: 14,
      rightTop: 86,
      leftBottom: 8,
      rightBottom: 92,
      topInset: 6,
      bottomInset: 6,
      sideTop: 18,
      sideBottom: 88,
      radiusTopOuter: 18,
      radiusTopInner: 30,
      radiusBottomOuter: 24,
      radiusBottomInner: 20,
    },
    angry: {
      width: 150,
      height: 128,
      openScale: 0.8,
      widthScale: 1.12,
      slant: 20,
      leftTop: 8,
      rightTop: 92,
      leftBottom: 20,
      rightBottom: 80,
      topInset: 8,
      bottomInset: 8,
      sideTop: 18,
      sideBottom: 82,
      radiusTopOuter: 12,
      radiusTopInner: 12,
      radiusBottomOuter: 22,
      radiusBottomInner: 22,
    },
    surprised: {
      width: 130,
      height: 178,
      openScale: 1.08,
      widthScale: 0.96,
      slant: 0,
      leftTop: 18,
      rightTop: 82,
      leftBottom: 18,
      rightBottom: 82,
      topInset: 0,
      bottomInset: 0,
      sideTop: 14,
      sideBottom: 86,
      radiusTopOuter: 30,
      radiusTopInner: 30,
      radiusBottomOuter: 30,
      radiusBottomInner: 30,
    },
    sleepy: {
      width: 164,
      height: 76,
      openScale: 0.58,
      widthScale: 1.14,
      slant: 0,
      leftTop: 14,
      rightTop: 86,
      leftBottom: 14,
      rightBottom: 86,
      topInset: 22,
      bottomInset: 22,
      sideTop: 34,
      sideBottom: 66,
      radiusTopOuter: 24,
      radiusTopInner: 24,
      radiusBottomOuter: 24,
      radiusBottomInner: 24,
    },
    curious: {
      width: 148,
      height: 152,
      openScale: 0.96,
      widthScale: 1.04,
      slant: 8,
      leftTop: 18,
      rightTop: 82,
      leftBottom: 12,
      rightBottom: 88,
      topInset: 4,
      bottomInset: 0,
      sideTop: 20,
      sideBottom: 84,
      radiusTopOuter: 22,
      radiusTopInner: 28,
      radiusBottomOuter: 18,
      radiusBottomInner: 18,
    },
    love: {
      width: 144,
      height: 148,
      openScale: 0.9,
      widthScale: 1.06,
      slant: 6,
      leftTop: 16,
      rightTop: 84,
      leftBottom: 10,
      rightBottom: 90,
      topInset: 6,
      bottomInset: 6,
      sideTop: 22,
      sideBottom: 84,
      radiusTopOuter: 28,
      radiusTopInner: 28,
      radiusBottomOuter: 26,
      radiusBottomInner: 26,
    },
    thinking: {
      width: 152,
      height: 118,
      openScale: 0.76,
      widthScale: 1.18,
      slant: 10,
      leftTop: 14,
      rightTop: 86,
      leftBottom: 8,
      rightBottom: 92,
      topInset: 18,
      bottomInset: 12,
      sideTop: 28,
      sideBottom: 74,
      radiusTopOuter: 18,
      radiusTopInner: 18,
      radiusBottomOuter: 18,
      radiusBottomInner: 18,
    },
  };

  return presets[emotion] ?? presets.neutral;
}

function polygonFromPoints(points) {
  return `polygon(${points.map(([x, y]) => `${x}% ${y}%`).join(", ")})`;
}

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(value, maximum));
}

boot().catch((error) => {
  console.error(error);
});
