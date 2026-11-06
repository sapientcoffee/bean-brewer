/**
 * Coffee Mood Catalog
 * Pure client-side catalog mapping human mood states to specialty coffee recipes.
 * Conforms to contracts/coffee-mood-schema.json.
 */

export const COFFEE_MOODS = [
  {
    mood_id: "sluggish",
    name: "Light Roast Ethiopian Yirgacheffe",
    tagline: "High acidity, clean bergamot sparkle to awaken brain fog",
    coffee_origin: "Yirgacheffe, Gedeo Zone, Ethiopia",
    roast_level: "Light",
    brew_method: "V60 Pour-Over",
    ratio: 16.0,
    water_temp_c: 93,
    grind_size: "Medium-Fine",
    tasting_notes: ["Bergamot", "Jasmine", "Meyer Lemon", "Peach Tea"],
    brew_seconds: 180,
    lore: "Grown at 2,000 meters above sea level, washed Yirgacheffe delivers intense floral aromatics and lively citric vibrancy that cuts through lethargy."
  },
  {
    mood_id: "focus",
    name: "Washed Colombian Huila",
    tagline: "Smooth milk chocolate sweetness and balanced body for deep work",
    coffee_origin: "Huila, Colombia",
    roast_level: "Medium",
    brew_method: "AeroPress (Inverted)",
    ratio: 14.5,
    water_temp_c: 90,
    grind_size: "Medium",
    tasting_notes: ["Milk Chocolate", "Red Apple", "Brown Sugar", "Toasted Pecan"],
    brew_seconds: 150,
    lore: "Rich volcanic soil yields balanced sweetness and medium body, perfect for prolonged concentration without over-stimulating jitters."
  },
  {
    mood_id: "stressed",
    name: "Swiss Water Decaf Sumatra Mandheling",
    tagline: "Deep grounding cedar, dark cocoa warmth with zero caffeine spike",
    coffee_origin: "Aceh & Lake Toba, Sumatra",
    roast_level: "Medium-Dark",
    brew_method: "French Press",
    ratio: 15.0,
    water_temp_c: 95,
    grind_size: "Coarse",
    tasting_notes: ["Cedar Wood", "Dark Cocoa", "Pipe Tobacco", "Molasses"],
    brew_seconds: 240,
    lore: "Wet-hulled Giling Basah processing creates heavy, velvety mouthfeel and soothing earthy tones without caffeine to lower cortisol."
  },
  {
    mood_id: "creative",
    name: "Anaerobic Natural Costa Rican Tarrazú",
    tagline: "Exotic tropical fruit explosion to spark associative thinking",
    coffee_origin: "Tarrazú Valley, Costa Rica",
    roast_level: "Medium-Light",
    brew_method: "Chemex",
    ratio: 15.5,
    water_temp_c: 92,
    grind_size: "Medium-Coarse",
    tasting_notes: ["Strawberry Guava", "Passionfruit", "Rum Raisin", "Cacao Nibs"],
    brew_seconds: 210,
    lore: "Sealed anaerobic fermentation tanks allow indigenous yeasts to develop wildly playful fruit esters and winey sweetness."
  },
  {
    mood_id: "social",
    name: "Guatemalan Antigua Huehuetenango",
    tagline: "Caramel praline and velvet crema crafted for shared warmth",
    coffee_origin: "Antigua, Guatemala",
    roast_level: "Medium",
    brew_method: "Espresso Cortado",
    ratio: 2.0,
    water_temp_c: 93,
    grind_size: "Fine",
    tasting_notes: ["Caramel", "Candied Orange", "Milk Chocolate", "Hazelnut"],
    brew_seconds: 30,
    lore: "Volcanic ash-enriched soil provides dense bean structure and honeyed sweetness that blends harmoniously with steamed silky milk."
  },
  {
    mood_id: "midnight",
    name: "Slow-Drip New Orleans Chicory & Bourbon",
    tagline: "Caramelized chicory and toasted oats for late-night companionship",
    coffee_origin: "Bourbon Santos Blend, Brazil",
    roast_level: "Dark",
    brew_method: "Moka Pot & Warm Oat Milk",
    ratio: 12.0,
    water_temp_c: 96,
    grind_size: "Fine-Medium",
    tasting_notes: ["Caramelized Chicory", "Toasted Oats", "Smoked Vanilla", "Dark Molasses"],
    brew_seconds: 180,
    lore: "French-market tradition blending French-roast Arabica with roasted chicory root for an unctuous, grounding midnight brew."
  }
];

export function getRecipeByMood(moodId) {
  const match = COFFEE_MOODS.find(m => m.mood_id === moodId);
  return match || COFFEE_MOODS.find(m => m.mood_id === "focus");
}
