import React, { useState, useEffect, useCallback } from 'react';
import { Box, ToggleButtonGroup, ToggleButton, Typography, Stack } from '@mui/material';
import StatsCards from './StatsCards';
import WeatherChart from './WeatherChart';
import AdvancedCharts from './AdvancedCharts';
import HistoricalView from './HistoricalView';
import { fetchCurrentWeather, fetchTrends, fetchStats } from '../services/api';

const REFRESH_INTERVAL = 60_000;

export default function Dashboard({ selectedLocation, temperatureUnit }) {
  const [currentWeather, setCurrentWeather] = useState(null);
  const [trends, setTrends] = useState([]);
  const [stats, setStats] = useState([]);
  const [loadingCurrent, setLoadingCurrent] = useState(true);
  const [loadingTrends, setLoadingTrends] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  const [period, setPeriod] = useState('daily');

  const loadData = useCallback(async () => {
    setLoadingCurrent(true);
    setLoadingTrends(true);
    setLoadingStats(true);

    try {
      const [currentRes, trendsRes, statsRes] = await Promise.all([
        fetchCurrentWeather(selectedLocation),
        fetchTrends(selectedLocation, 7),
        fetchStats(selectedLocation, period),
      ]);

      const current = currentRes.data;
      setCurrentWeather(Array.isArray(current) ? current[0] : current);
      setTrends(trendsRes.data || []);
      setStats(statsRes.data || []);
    } catch {
      // errors handled by individual components
    } finally {
      setLoadingCurrent(false);
      setLoadingTrends(false);
      setLoadingStats(false);
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
    </Box>
  );
}
