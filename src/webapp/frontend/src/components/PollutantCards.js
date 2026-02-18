import React from 'react';
import { Card, CardContent, Typography, Grid, Skeleton, Box } from '@mui/material';
import GrainIcon from '@mui/icons-material/Grain';
import BlurOnIcon from '@mui/icons-material/BlurOn';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';
import ScienceIcon from '@mui/icons-material/Science';
import FactoryIcon from '@mui/icons-material/Factory';
import LocalGasStationIcon from '@mui/icons-material/LocalGasStation';

const cards = [
  { key: 'pm25', label: 'PM2.5', unit: 'ug/m3', icon: GrainIcon, color: '#e53935', format: (v) => (v != null ? v.toFixed(1) : '--') },
  { key: 'pm10', label: 'PM10', unit: 'ug/m3', icon: BlurOnIcon, color: '#1e88e5', format: (v) => (v != null ? v.toFixed(1) : '--') },
  { key: 'o3', label: 'Ozone', unit: 'ppb', icon: CloudQueueIcon, color: '#43a047', format: (v) => (v != null ? v.toFixed(1) : '--') },
  { key: 'no2', label: 'NO2', unit: 'ppb', icon: ScienceIcon, color: '#fb8c00', format: (v) => (v != null ? v.toFixed(1) : '--') },
  { key: 'so2', label: 'SO2', unit: 'ppb', icon: FactoryIcon, color: '#8e24aa', format: (v) => (v != null ? v.toFixed(1) : '--') },
  { key: 'co', label: 'CO', unit: 'ppm', icon: LocalGasStationIcon, color: '#546e7a', format: (v) => (v != null ? v.toFixed(2) : '--') },
];

export default function PollutantCards({ data, loading }) {
  return (
    <Grid container spacing={2}>
      {cards.map(({ key, label, unit, icon: Icon, color, format }) => (
        <Grid item xs={6} sm={4} md={2} key={key}>
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
                <Icon sx={{ color, mr: 1, fontSize: 24 }} />
                <Typography variant="body2" color="text.secondary">
                  {label}
                </Typography>
              </Box>
              {loading ? (
                <Skeleton variant="text" width={60} height={40} />
              ) : (
                <Typography variant="h5" fontWeight="bold">
                  {format(data?.[key])}
                  <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
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
