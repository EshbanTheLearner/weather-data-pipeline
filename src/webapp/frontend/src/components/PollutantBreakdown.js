import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { Paper, Typography, Skeleton, Box, useTheme } from '@mui/material';

const POLLUTANT_COLORS = {
  pm25: '#e53935',
  pm10: '#1e88e5',
  o3: '#43a047',
  no2: '#fb8c00',
  so2: '#8e24aa',
  co: '#546e7a',
};

const POLLUTANT_LABELS = {
  pm25: 'PM2.5',
  pm10: 'PM10',
  o3: 'O3',
  no2: 'NO2',
  so2: 'SO2',
  co: 'CO',
};

export default function PollutantBreakdown({ data, loading }) {
  const theme = useTheme();
  const darkMode = theme.palette.mode === 'dark';
  const gridStroke = darkMode ? '#333' : '#eee';
  const tickFill = darkMode ? '#aaa' : '#666';
  const tooltipBg = darkMode ? '#1e1e1e' : '#fff';
  const tooltipBorder = darkMode ? '#444' : '#ccc';
  const tooltipColor = darkMode ? '#eee' : '#333';

  if (loading) {
    return (
      <Paper sx={{ p: 3 }}>
        <Skeleton variant="text" width={200} height={32} />
        <Skeleton variant="rectangular" height={300} sx={{ mt: 2 }} />
      </Paper>
    );
  }

  if (!data) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Pollutant Breakdown
        </Typography>
        <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography color="text.secondary">No pollutant data available</Typography>
        </Box>
      </Paper>
    );
  }

  const chartData = Object.entries(POLLUTANT_LABELS)
    .map(([key, label]) => ({
      name: label,
      value: data[key] != null ? Number(data[key]) : 0,
      key,
    }))
    .filter((d) => d.value > 0);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Pollutant Breakdown
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="name" tick={{ fontSize: 12, fill: tickFill }} />
          <YAxis tick={{ fontSize: 12, fill: tickFill }} />
          <Tooltip
            contentStyle={{
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              backgroundColor: tooltipBg,
              borderColor: tooltipBorder,
              color: tooltipColor,
            }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry) => (
              <Cell key={entry.key} fill={POLLUTANT_COLORS[entry.key]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
}
