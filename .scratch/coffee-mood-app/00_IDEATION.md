---
id: 00_IDEATION
type: ideation
name: Coffee Mood Selection Web App Ideation
description: Product ideation and user experience framing for Coffee Mood Selection
  Web App
status: draft
stage: 0_ideation
generated:
  by: bean-roaster/ideator
  at: '2026-11-06T16:36:51Z'
stages_completed:
  0_triage: cortado/greenfield
  0_ideation: bean-roaster/ideator (2026-11-06T16:36:51Z)
---

# ☕ Green Bean Selection: Coffee Mood Selection Web App (`00_IDEATION`)

## 1. Problem Space & User Motivations
Coffee drinkers often default to the same drink out of routine rather than matching their physiological, cognitive, and emotional state. When facing different work modes—such as a high-intensity debugging session, creative brainstorming, stress relief, or evening focus—the wrong coffee preparation (e.g. high-acidity triple shot during acute anxiety, or an oversweetened milk drink during sluggish lethargy) degrades performance and wellbeing.

The **Coffee Mood Selection Web App** bridges mood psychology with specialty coffee craft. It guides users through an intuitive, aesthetic mood selector, matches them with the ideal specialty roast, extraction method, brew parameters, and sensory lore, and provides an integrated brew timer.

## 2. Core User Personas & Mood States

| Mood State | Cognitive Need | Recommended Coffee Pairing | Brew Method | Sensory Profile |
| :--- | :--- | :--- | :--- | :--- |
| **Sluggish / Brain Fog** | Fast kickstart, sharp focus | Light Roast Ethiopian Yirgacheffe | V60 Pour-over (1:16 ratio) | Bergamot, jasmine, crisp citrus acidity |
| **Deep Focus / Flow State** | Sustained clarity, low jitter | Medium Roast Colombian Huila | Aeropress (Inverted, 2:30 brew) | Milk chocolate, red apple, sweet cane sugar |
| **Stressed / Overwhelmed** | Calming ritual, grounding warmth | Swiss Water Decaf or Half-Caf Sumatra | French Press (4:00 steep) | Earthy, cocoa, cedar, low acidity |
| **Creative / Daydreaming** | Novelty, olfactory stimulation | Anaerobic Natural Costa Rican | Chemex (Slow bloom, 1:15) | Tropical fruit, passionfruit, strawberry wine |
| **Social / Celebratory** | Indulgent, shared delight | Dark Roast Cortado or Flat White | Espresso (1:2 ratio with microfoam) | Dark chocolate fudge, roasted hazelnut, velvet body |
| **Midnight Oil / Late Night** | Warm comforting companion, low stimulant | Light Roast Chicory & Oat Café au Lait | Moka Pot / Warm Steamer | Toasted oats, caramelized chicory, spiced cardamom |

## 3. Key Functional Deliverables
1. **Interactive Mood Grid**: Visual cards with rich emoji/coffee icons and mood descriptions.
2. **Dynamic Pairing Card**: Instantly computes and displays the recommended roast, grind size, coffee-to-water ratio, and tasting notes.
3. **Interactive Step-by-Step Brew Timer**: Start/pause/reset timer with active bloom and pour phase indicators.
4. **Preference Modifiers**: Toggles for Temperature (Hot / Iced), Serving Size (Single Cup 250ml / Double 500ml), and Caffeine Preference (Full Caf / Half-Caf / Decaf).
5. **Pure Client-Side Architecture**: Standalone, responsive HTML5/CSS3/JavaScript web app with zero external npm dependencies or telemetry leaks.
