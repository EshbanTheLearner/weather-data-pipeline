/**
 * Convert a Celsius value to the target unit.
 * @param {number|null} value  Temperature in Celsius
 * @param {'C'|'F'} unit       Target unit
 * @returns {number|null}
 */
export function convertTemp(value, unit) {
  if (value == null) return null;
  return unit === 'F' ? value * 9 / 5 + 32 : value;
}

/**
 * Format a temperature value with its unit symbol.
 * @param {number|null} value  Temperature in Celsius
 * @param {'C'|'F'} unit       Target unit
 * @param {number} [decimals=1] Decimal places
 * @returns {string}
 */
export function formatTemp(value, unit, decimals = 1) {
  const converted = convertTemp(value, unit);
  if (converted == null) return '--';
  return `${converted.toFixed(decimals)} ${tempUnit(unit)}`;
}

/**
 * Return the unit symbol string.
 * @param {'C'|'F'} unit
 * @returns {string}
 */
export function tempUnit(unit) {
  return unit === 'F' ? '°F' : '°C';
}
