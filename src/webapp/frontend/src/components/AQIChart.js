import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceArea,
} from 'recharts';
import { Paper, Typography, Skeleton, Box, useTheme } from '@mui/material';
import { formatShortDate } from '../utils/dateFormatter';

const AQI_BANDS = [
  { y1: 0, y2: 50, fill: '#00e400', opacity: 0.1 },
  { y1: 50, y2: 100, fill: '#ffff00', opacity: 0.1 },
  { y1: 100, y2: 150, fill: '#ff7e00', opacity: 0.1 },
  { y1: 150, y2: 200, fill: '#ff0000', opacity: 0.1 },
  { y1: 200, y2: 300, fill: '#8f3f97', opacity: 0.1 },
];

export default function AQIChart({ data, loading }) {
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
          AQI Trends (7 Days)
        </Typography>
        <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography color="text.secondary">No air quality trend data available</Typography>
        </Box>
      </Paper>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    date: formatShortDate(d.date),
  }));

  const maxAqi = Math.max(...data.map((d) => d.max_aqi || d.avg_aqi || 0), 100);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        AQI Trends (7 Days)
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          {AQI_BANDS.filter((b) => b.y1 < maxAqi).map((band) => (
            <ReferenceArea
              key={band.y1}
              y1={band.y1}
              y2={Math.min(band.y2, maxAqi)}
              fill={band.fill}
              fillOpacity={band.opacity}
            />
          ))}
          <XAxis dataKey="date" tick={{ fontSize: 12, fill: tickFill }} />
          <YAxis
            domain={[0, Math.ceil(maxAqi / 50) * 50]}
            tick={{ fontSize: 12, fill: tickFill }}
            label={{ value: 'AQI', position: 'insideLeft', offset: 10, fill: tickFill }}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              backgroundColor: tooltipBg,
              borderColor: tooltipBorder,
              color: tooltipColor,
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="avg_aqi"
            name="Avg AQI"
            stroke="#1976d2"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="max_aqi"
            name="Max AQI"
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
