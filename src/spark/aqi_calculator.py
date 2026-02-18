"""
EPA Air Quality Index (AQI) Calculator.

Provides utility functions for computing AQI sub-indices and the overall
AQI value from individual pollutant concentrations, following the EPA
standard breakpoint-based linear interpolation method.

Supported pollutants:
    PM2.5 (24-hr, ug/m3), PM10 (24-hr, ug/m3), O3 (8-hr, ppb),
    NO2 (1-hr, ppb), SO2 (1-hr, ppb), CO (8-hr, ppm)
"""

# ---------------------------------------------------------------------------
# EPA AQI breakpoint tables
# ---------------------------------------------------------------------------
# Each entry is a list of (C_low, C_high, I_low, I_high) tuples where:
#   C_low, C_high  = concentration breakpoints for the pollutant
#   I_low, I_high  = corresponding AQI index breakpoints

AQI_BREAKPOINTS = {
    "pm25": [
        (0,     12.0,   0,   50),
        (12.1,  35.4,   51,  100),
        (35.5,  55.4,   101, 150),
        (55.5,  150.4,  151, 200),
        (150.5, 250.4,  201, 300),
        (250.5, 500.4,  301, 500),
    ],
    "pm10": [
        (0,   54,   0,   50),
        (55,  154,  51,  100),
        (155, 254,  101, 150),
        (255, 354,  151, 200),
        (355, 424,  201, 300),
        (425, 604,  301, 500),
    ],
    "o3": [
        (0,   54,   0,   50),
        (55,  70,   51,  100),
        (71,  85,   101, 150),
        (86,  105,  151, 200),
        (106, 200,  201, 300),
    ],
    "no2": [
        (0,    53,    0,   50),
        (54,   100,   51,  100),
        (101,  360,   101, 150),
        (361,  649,   151, 200),
        (650,  1249,  201, 300),
        (1250, 2049,  301, 500),
    ],
    "so2": [
        (0,   35,    0,   50),
        (36,  75,    51,  100),
        (76,  185,   101, 150),
        (186, 304,   151, 200),
        (305, 604,   201, 300),
        (605, 1004,  301, 500),
    ],
    "co": [
        (0,    4.4,   0,   50),
        (4.5,  9.4,   51,  100),
        (9.5,  12.4,  101, 150),
        (12.5, 15.4,  151, 200),
        (15.5, 30.4,  201, 300),
        (30.5, 50.4,  301, 500),
    ],
}

# ---------------------------------------------------------------------------
# AQI category labels
# ---------------------------------------------------------------------------
AQI_CATEGORIES = [
    (0,   50,  "Good"),
    (51,  100, "Moderate"),
    (101, 150, "Unhealthy for Sensitive Groups"),
    (151, 200, "Unhealthy"),
    (201, 300, "Very Unhealthy"),
    (301, 500, "Hazardous"),
]


def _get_category(aqi_value: int) -> str:
    """Return the EPA category label for a given AQI value."""
    for lo, hi, label in AQI_CATEGORIES:
        if lo <= aqi_value <= hi:
            return label
    return "Hazardous"


# ---------------------------------------------------------------------------
# Sub-index calculation
# ---------------------------------------------------------------------------

def calculate_sub_index(pollutant: str, concentration: float) -> int:
    """Calculate the AQI sub-index for a single pollutant.

    Uses EPA linear interpolation:
        I = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low

    Args:
        pollutant: Pollutant key (pm25, pm10, o3, no2, so2, co).
        concentration: Measured concentration value.

    Returns:
        Integer AQI sub-index, or -1 if the pollutant is unknown or
        the concentration is out of range.
    """
    if pollutant not in AQI_BREAKPOINTS:
        return -1

    breakpoints = AQI_BREAKPOINTS[pollutant]
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= concentration <= c_high:
            aqi = ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low) + i_low
            return round(aqi)

    # Concentration out of defined range
    return -1


# ---------------------------------------------------------------------------
# Overall AQI calculation
# ---------------------------------------------------------------------------

def calculate_aqi(
    pm25: float | None = None,
    pm10: float | None = None,
    o3: float | None = None,
    no2: float | None = None,
    so2: float | None = None,
    co: float | None = None,
) -> dict:
    """Calculate the overall AQI from individual pollutant concentrations.

    The overall AQI is the maximum of all valid sub-indices.  The dominant
    pollutant is the one that produced the highest sub-index.

    Args:
        pm25: PM2.5 concentration (ug/m3), optional.
        pm10: PM10 concentration (ug/m3), optional.
        o3: Ozone concentration (ppb), optional.
        no2: NO2 concentration (ppb), optional.
        so2: SO2 concentration (ppb), optional.
        co: CO concentration (ppm), optional.

    Returns:
        dict with keys:
            aqi               - Overall AQI value (int).
            category          - EPA category label (str).
            dominant_pollutant - Pollutant with the highest sub-index (str).
    """
    pollutant_values = {
        "pm25": pm25,
        "pm10": pm10,
        "o3": o3,
        "no2": no2,
        "so2": so2,
        "co": co,
    }

    sub_indices: dict[str, int] = {}
    for name, value in pollutant_values.items():
        if value is not None:
            idx = calculate_sub_index(name, value)
            if idx >= 0:
                sub_indices[name] = idx

    if not sub_indices:
        return {"aqi": 0, "category": "Good", "dominant_pollutant": "none"}

    dominant = max(sub_indices, key=sub_indices.get)
    overall_aqi = sub_indices[dominant]
    category = _get_category(overall_aqi)

    return {
        "aqi": overall_aqi,
        "category": category,
        "dominant_pollutant": dominant,
    }
