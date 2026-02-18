import React, { useState, useEffect, useCallback } from 'react';
import { Box, ToggleButtonGroup, ToggleButton, Typography, Stack, Divider } from '@mui/material';
import StatsCards from './StatsCards';
import WeatherChart from './WeatherChart';
import AdvancedCharts from './AdvancedCharts';
import HistoricalView from './HistoricalView';
import AirQualityCard from './AirQualityCard';
import PollutantCards from './PollutantCards';
import AQIChart from './AQIChart';
import PollutantBreakdown from './PollutantBreakdown';
import AirQualityHistorical from './AirQualityHistorical';
import { fetchCurrentWeather, fetchTrends, fetchStats, fetchCurrentAirQuality, fetchAirQualityTrends } from '../services/api';

const REFRESH_INTERVAL = 60_000;

export default function Dashboard({ selectedLocation, temperatureUnit }) {
  const [currentWeather, setCurrentWeather] = useState(null);
  const [trends, setTrends] = useState([]);
  const [stats, setStats] = useState([]);
  const [loadingCurrent, setLoadingCurrent] = useState(true);
  const [loadingTrends, setLoadingTrends] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  const [period, setPeriod] = useState('daily');

  const [currentAirQuality, setCurrentAirQuality] = useState(null);
  const [aqiTrends, setAqiTrends] = useState([]);
  const [loadingAQ, setLoadingAQ] = useState(true);
  const [loadingAQTrends, setLoadingAQTrends] = useState(true);

  const loadData = useCallback(async () => {
    setLoadingCurrent(true);
    setLoadingTrends(true);
    setLoadingStats(true);
    setLoadingAQ(true);
    setLoadingAQTrends(true);

    try {
      const [currentRes, trendsRes, statsRes, aqRes, aqTrendsRes] = await Promise.all([
        fetchCurrentWeather(selectedLocation),
        fetchTrends(selectedLocation, 7),
        fetchStats(selectedLocation, period),
        fetchCurrentAirQuality(selectedLocation),
        fetchAirQualityTrends(selectedLocation, 7),
      ]);

      const current = currentRes.data;
      setCurrentWeather(Array.isArray(current) ? current[0] : current);
      setTrends(trendsRes.data || []);
      setStats(statsRes.data || []);

      const aqCurrent = aqRes.data;
      setCurrentAirQuality(Array.isArray(aqCurrent) ? aqCurrent[0] : aqCurrent);
      setAqiTrends(aqTrendsRes.data || []);
    } catch {
      // errors handled by individual components
    } finally {
      setLoadingCurrent(false);
      setLoadingTrends(false);
      setLoadingStats(false);
      setLoadingAQ(false);
      setLoadingAQTrends(false);
    }
  }, [selectedLocation, period]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [loadData]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <StatsCards data={currentWeather} loading={loadingCurrent} temperatureUnit={temperatureUnit} />

      <WeatherChart data={trends} loading={loadingTrends} temperatureUnit={temperatureUnit} />

      <Stack direction="row" alignItems="center" spacing={2}>
        <Typography variant="subtitle2" color="text.secondary">
          Aggregation Period:
        </Typography>
        <ToggleButtonGroup
          value={period}
          exclusive
          onChange={(_, v) => { if (v) setPeriod(v); }}
          size="small"
        >
          <ToggleButton value="hourly">Hourly</ToggleButton>
          <ToggleButton value="daily">Daily</ToggleButton>
        </ToggleButtonGroup>
      </Stack>

      <AdvancedCharts data={stats} loading={loadingStats} temperatureUnit={temperatureUnit} />

      <HistoricalView locationId={selectedLocation} temperatureUnit={temperatureUnit} />

      <Divider sx={{ my: 1 }} />

      <Typography variant="h5" fontWeight={600}>Air Quality</Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 2fr' }, gap: 2 }}>
        <AirQualityCard data={currentAirQuality} loading={loadingAQ} />
        <PollutantCards data={currentAirQuality} loading={loadingAQ} />
      </Box>

      <AQIChart data={aqiTrends} loading={loadingAQTrends} />

      <PollutantBreakdown data={currentAirQuality} loading={loadingAQ} />

      <AirQualityHistorical locationId={selectedLocation} />
    </Box>
  );
}
