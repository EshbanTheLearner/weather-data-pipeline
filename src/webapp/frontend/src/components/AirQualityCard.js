import React from 'react';
import { Card, CardContent, Typography, Box, Skeleton, Chip } from '@mui/material';
import { getAQIColor, getAQICategory, getAQIDescription } from '../utils/aqiUtils';

export default function AirQualityCard({ data, loading }) {
  const aqi = data?.aqi;
  const color = getAQIColor(aqi);
  const category = getAQICategory(aqi);
  const description = getAQIDescription(aqi);
  const dominant = data?.dominant_pollutant?.toUpperCase() || '--';

  return (
    <Card
      sx={{
        borderTop: `4px solid ${color}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        transition: 'transform 0.2s',
        '&:hover': { transform: 'translateY(-2px)' },
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6">Air Quality Index</Typography>
          {!loading && (
            <Chip
              label={category}
              sx={{ bgcolor: color, color: aqi > 100 ? '#fff' : '#000', fontWeight: 'bold' }}
            />
          )}
        </Box>
        {loading ? (
          <Skeleton variant="text" width={120} height={64} />
        ) : (
          <>
            <Typography variant="h2" fontWeight="bold" sx={{ color }}>
              {aqi != null ? aqi : '--'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {description}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Dominant pollutant: <strong>{dominant}</strong>
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  );
}
