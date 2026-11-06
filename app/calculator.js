/**
 * Recipe Calculator
 * Pure math calculations for water volume and dry coffee dosage.
 */

export function calculateBrewDosage({ ratio, servings = 1, isIced = false, baseVolumePerServing = 250 }) {
  const safeServings = Math.max(1, Math.min(4, Number(servings) || 1));
  const safeRatio = Math.max(1, Number(ratio) || 15);

  let totalWaterVolume = baseVolumePerServing * safeServings;
  let hotWaterVolume = totalWaterVolume;
  let iceVolume = 0;

  if (isIced) {
    hotWaterVolume = Math.round(totalWaterVolume * 0.6);
    iceVolume = totalWaterVolume - hotWaterVolume;
  }

  // Calculate coffee dosage in grams rounded to 1 decimal place
  const coffeeGrams = Number((totalWaterVolume / safeRatio).toFixed(1));

  return {
    servings: safeServings,
    totalWaterVolume,
    hotWaterVolume,
    iceVolume,
    coffeeGrams,
    ratio: safeRatio
  };
}
