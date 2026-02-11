import React from 'react';
import { Card, CardContent, Typography, Grid, Skeleton, Box } from '@mui/material';
import ThermostatIcon from '@mui/icons-material/Thermostat';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import AirIcon from '@mui/icons-material/Air';
import SpeedIcon from '@mui/icons-material/Speed';
import { convertTemp, tempUnit } from '../utils/temperatureUtils';

const cards = (temperatureUnit) => [
  {
    key: 'temperature',
    label: 'Temperature',
    unit: tempUnit(temperatureUnit),
    icon: ThermostatIcon,
    color: '#e53935',
    format: (v) => (v != null ? convertTemp(v, temperatureUnit).toFixed(1) : '--'),
  },
  {
    key: 'humidity',
    label: 'Humidity',
    unit: '%',
    icon: WaterDropIcon,
    color: '#1e88e5',
    format: (v) => (v != null ? v.toFixed(1) : '--'),
  },
  {
    key: 'wind_speed',
    label: 'Wind Speed',
    unit: 'm/s',
    icon: AirIcon,
    color: '#43a047',
    format: (v) => (v != null ? v.toFixed(1) : '--'),
  },
  {
    key: 'pressure',
    label: 'Pressure',
    unit: 'hPa',
    icon: SpeedIcon,
    color: '#fb8c00',
    format: (v) => (v != null ? v.toFixed(0) : '--'),
  },
];

export default function StatsCards({ data, loading, temperatureUnit }) {
  return (
    <Grid container spacing={2}>
      {cards(temperatureUnit).map(({ key, label, unit, icon: Icon, color, format }) => (
        <Grid item xs={12} sm={6} md={3} key={key}>
          <Card
            sx={{
              borderTop: `4px solid ${color}`,
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              transition: 'transform 0.2s',
              '&:hover': { transform: 'translateY(-2px)' },
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Icon sx={{ color, mr: 1, fontSize: 28 }} />
                <Typography variant="body2" color="text.secondary">
                  {label}
                </Typography>
              </Box>
              {loading ? (
                <Skeleton variant="text" width={80} height={48} />
              ) : (
                <Typography variant="h4" fontWeight="bold">
                  {format(data?.[key])}
                  <Typography component="span" variant="body1" color="text.secondary" sx={{ ml: 0.5 }}>
                    {unit}
                  </Typography>
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}
