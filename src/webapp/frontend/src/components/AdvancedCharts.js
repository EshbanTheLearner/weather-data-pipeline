import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ComposedChart, Line, Bar,
} from 'recharts';
import { Paper, Typography, Grid, Box, Skeleton } from '@mui/material';
import { formatShortDate } from '../utils/dateFormatter';

const COLORS = {
  temperature: '#1976d2',
  humidity: '#43a047',
  wind: '#00897b',
  pressure: '#fb8c00',
};

function ChartWrapper({ title, loading, isEmpty, height = 280, children }) {
  if (loading) {
    return (
      <Paper sx={{ p: 2 }}>
        <Skeleton variant="text" width={180} height={28} />
        <Skeleton variant="rectangular" height={height} sx={{ mt: 1 }} />
      </Paper>
    );
  }
  if (isEmpty) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle1" fontWeight={600}>{title}</Typography>
        <Box sx={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography color="text.secondary">No data available</Typography>
        </Box>
      </Paper>
    );
  }
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
        {title}
      </Typography>
      {children}
    </Paper>
  );
}

export default function AdvancedCharts({ data, loading }) {
  const chartData = (data || []).map((d) => ({
    ...d,
    date: formatShortDate(d.bucket),
  }));

  const empty = !data || data.length === 0;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <ChartWrapper title="Temperature & Humidity" loading={loading} isEmpty={empty}>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id="gradTemp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.temperature} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS.temperature} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradHumid" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.humidity} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS.humidity} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="temp" tick={{ fontSize: 11 }} label={{ value: '°C', position: 'insideLeft', offset: 10, fontSize: 11 }} />
              <YAxis yAxisId="humid" orientation="right" tick={{ fontSize: 11 }} label={{ value: '%', position: 'insideRight', offset: 10, fontSize: 11 }} />
              <Tooltip
                contentStyle={{ borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
                formatter={(v, name) => {
                  const u = name === 'avg_humidity' ? '%' : '°C';
                  return [`${Number(v).toFixed(1)} ${u}`, name === 'avg_humidity' ? 'Humidity' : 'Temperature'];
                }}
              />
              <Legend formatter={(v) => (v === 'avg_temperature' ? 'Temperature' : 'Humidity')} />
              <Area yAxisId="temp" type="monotone" dataKey="avg_temperature" stroke={COLORS.temperature} fill="url(#gradTemp)" strokeWidth={2} />
              <Area yAxisId="humid" type="monotone" dataKey="avg_humidity" stroke={COLORS.humidity} fill="url(#gradHumid)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartWrapper>
      </Grid>

      <Grid item xs={12} md={6}>
        <ChartWrapper title="Wind Speed & Pressure" loading={loading} isEmpty={empty}>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="wind" tick={{ fontSize: 11 }} label={{ value: 'm/s', position: 'insideLeft', offset: 10, fontSize: 11 }} />
              <YAxis yAxisId="pres" orientation="right" tick={{ fontSize: 11 }} domain={['auto', 'auto']} label={{ value: 'hPa', position: 'insideRight', offset: 10, fontSize: 11 }} />
              <Tooltip
                contentStyle={{ borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
                formatter={(v, name) => {
                  const u = name === 'avg_pressure' ? 'hPa' : 'm/s';
                  const l = name === 'avg_pressure' ? 'Pressure' : 'Wind Speed';
                  return [`${Number(v).toFixed(1)} ${u}`, l];
                }}
              />
              <Legend formatter={(v) => (v === 'avg_pressure' ? 'Pressure' : 'Wind Speed')} />
              <Bar yAxisId="wind" dataKey="avg_wind_speed" fill={COLORS.wind} barSize={20} radius={[4, 4, 0, 0]} opacity={0.8} />
              <Line yAxisId="pres" type="monotone" dataKey="avg_pressure" stroke={COLORS.pressure} strokeWidth={2} dot={{ r: 3 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartWrapper>
      </Grid>
    </Grid>
  );
}
