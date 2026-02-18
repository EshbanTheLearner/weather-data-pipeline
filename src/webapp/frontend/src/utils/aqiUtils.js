/**
 * AQI color thresholds per EPA standard.
 */
const AQI_LEVELS = [
  { max: 50, color: '#00e400', label: 'Good', description: 'Air quality is satisfactory' },
  { max: 100, color: '#ffff00', label: 'Moderate', description: 'Acceptable air quality' },
  { max: 150, color: '#ff7e00', label: 'Unhealthy for Sensitive Groups', description: 'Sensitive groups may experience effects' },
  { max: 200, color: '#ff0000', label: 'Unhealthy', description: 'Everyone may experience health effects' },
  { max: 300, color: '#8f3f97', label: 'Very Unhealthy', description: 'Health alert: significant risk' },
  { max: 500, color: '#7e0023', label: 'Hazardous', description: 'Emergency conditions' },
];

export function getAQILevel(aqi) {
  if (aqi == null) return AQI_LEVELS[0];
  return AQI_LEVELS.find((l) => aqi <= l.max) || AQI_LEVELS[AQI_LEVELS.length - 1];
}

export function getAQIColor(aqi) {
  return getAQILevel(aqi).color;
}

export function getAQICategory(aqi) {
  return getAQILevel(aqi).label;
}

export function getAQIDescription(aqi) {
  return getAQILevel(aqi).description;
}
