import { COFFEE_MOODS, getRecipeByMood } from "./data/coffee_moods.js";
import { calculateBrewDosage } from "./calculator.js";
import { BrewTimer } from "./timer.js";

let activeMoodId = "focus";
let servings = 1;
let isIced = false;
let brewTimer = null;

function init() {
  renderMoodGrid();
  updateView(activeMoodId);
  setupEventListeners();
}

function renderMoodGrid() {
  const grid = document.getElementById("mood-grid");
  if (!grid) return;
  grid.innerHTML = "";

  const moodIcons = {
    sluggish: "⚡",
    focus: "🎯",
    stressed: "🌿",
    creative: "🎨",
    social: "☕",
    midnight: "🌙"
  };

  const moodLabels = {
    sluggish: "Sluggish",
    focus: "Deep Focus",
    stressed: "Stressed",
    creative: "Creative",
    social: "Social",
    midnight: "Midnight Oil"
  };

  COFFEE_MOODS.forEach(recipe => {
    const btn = document.createElement("button");
    btn.className = `mood-btn ${recipe.mood_id === activeMoodId ? "active" : ""}`;
    btn.setAttribute("data-mood", recipe.mood_id);
    btn.setAttribute("aria-label", `Select mood: ${moodLabels[recipe.mood_id]}`);
    btn.innerHTML = `
      <span class="mood-icon">${moodIcons[recipe.mood_id] || "☕"}</span>
      <span>${moodLabels[recipe.mood_id] || recipe.mood_id}</span>
    `;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".mood-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeMoodId = recipe.mood_id;
      updateView(activeMoodId);
    });
    grid.appendChild(btn);
  });
}

function updateView(moodId) {
  const recipe = getRecipeByMood(moodId);
  if (!recipe) return;

  const dosage = calculateBrewDosage({
    ratio: recipe.ratio,
    servings,
    isIced
  });

  // Update recipe header
  document.getElementById("recipe-name").textContent = recipe.name;
  document.getElementById("recipe-tagline").textContent = recipe.tagline;

  // Update specs
  document.getElementById("spec-origin").textContent = recipe.coffee_origin;
  document.getElementById("spec-roast").textContent = recipe.roast_level;
  document.getElementById("spec-method").textContent = recipe.brew_method;
  document.getElementById("spec-ratio").textContent = `1 : ${recipe.ratio}`;
  document.getElementById("spec-temp").textContent = `${recipe.water_temp_c} °C`;
  document.getElementById("spec-grind").textContent = recipe.grind_size;
  document.getElementById("spec-dose").textContent = `${dosage.coffeeGrams} g`;
  document.getElementById("spec-water").textContent = `${dosage.hotWaterVolume} ml ${dosage.iceVolume > 0 ? `(+ ${dosage.iceVolume}g ice)` : ""}`;

  // Update tasting notes
  const notesContainer = document.getElementById("tasting-notes");
  notesContainer.innerHTML = "";
  recipe.tasting_notes.forEach(note => {
    const span = document.createElement("span");
    span.className = "note-badge";
    span.textContent = note;
    notesContainer.appendChild(span);
  });

  // Update lore
  document.getElementById("recipe-lore").textContent = recipe.lore;

  // Initialize or reset timer
  initTimer(recipe.brew_seconds);
}

function initTimer(brewSeconds) {
  if (brewTimer) {
    brewTimer.reset(brewSeconds);
  } else {
    brewTimer = new BrewTimer({
      totalSeconds: brewSeconds,
      onTick: ({ remainingSeconds, phase }) => {
        document.getElementById("timer-display").textContent = brewTimer.formatTime(remainingSeconds);
        document.getElementById("timer-phase").textContent = phase;
      },
      onComplete: () => {
        document.getElementById("timer-display").textContent = "00:00";
        document.getElementById("timer-phase").textContent = "☕ Extraction complete! Enjoy your mood cup.";
      }
    });
  }
  document.getElementById("timer-display").textContent = brewTimer.formatTime(brewSeconds);
  document.getElementById("timer-phase").textContent = "Ready to brew";
}

function setupEventListeners() {
  document.getElementById("serving-select").addEventListener("change", (e) => {
    servings = parseInt(e.target.value, 10);
    updateView(activeMoodId);
  });

  document.getElementById("temp-select").addEventListener("change", (e) => {
    isIced = e.target.value === "iced";
    updateView(activeMoodId);
  });

  document.getElementById("timer-start").addEventListener("click", () => {
    brewTimer.start();
  });

  document.getElementById("timer-pause").addEventListener("click", () => {
    brewTimer.pause();
  });

  document.getElementById("timer-reset").addEventListener("click", () => {
    const recipe = getRecipeByMood(activeMoodId);
    brewTimer.reset(recipe.brew_seconds);
  });
}

// Auto-run if in browser
if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", init);
}
