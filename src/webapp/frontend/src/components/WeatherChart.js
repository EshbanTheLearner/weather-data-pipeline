import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { Paper, Typography, Skeleton, Box, useTheme } from '@mui/material';
import { formatShortDate } from '../utils/dateFormatter';
import { convertTemp, tempUnit } from '../utils/temperatureUtils';

export default function WeatherChart({ data, loading, temperatureUnit }) {
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

  if (!data || data.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Temperature Trends (7 Days)
        </Typography>
        <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography color="text.secondary">No trend data available</Typography>
        </Box>
      </Paper>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    date: formatShortDate(d.date),
    avg_temperature: convertTemp(d.avg_temperature, temperatureUnit),
    min_temperature: convertTemp(d.min_temperature, temperatureUnit),
    max_temperature: convertTemp(d.max_temperature, temperatureUnit),
  }));

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Temperature Trends (7 Days)
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="date" tick={{ fontSize: 12, fill: tickFill }} />
          <YAxis
            tick={{ fontSize: 12, fill: tickFill }}
            label={{ value: tempUnit(temperatureUnit), position: 'insideLeft', offset: 10, fill: tickFill }}
          />
          <Tooltip
            contentStyle={{ borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.15)', backgroundColor: tooltipBg, borderColor: tooltipBorder, color: tooltipColor }}
            formatter={(value, name) => {
              const labels = {
                avg_temperature: 'Avg',
                min_temperature: 'Min',
                max_temperature: 'Max',
              };
              return [`${Number(value).toFixed(1)} ${tempUnit(temperatureUnit)}`, labels[name] || name];
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="avg_temperature"
            name="Avg"
            stroke="#1976d2"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="min_temperature"
            name="Min"
            stroke="#90caf9"
            strokeWidth={1.5}
            strokeDasharray="5 5"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="max_temperature"
            name="Max"
            stroke="#e53935"
            strokeWidth={1.5}
            strokeDasharray="5 5"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </Paper>
  );
}
