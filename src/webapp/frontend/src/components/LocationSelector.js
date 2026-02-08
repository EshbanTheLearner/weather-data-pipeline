import React from 'react';
import { FormControl, Select, MenuItem, InputLabel } from '@mui/material';

export default function LocationSelector({ locations, selectedLocation, onLocationChange }) {
  return (
    <FormControl size="small" sx={{ minWidth: 180 }}>
      <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Location</InputLabel>
      <Select
        value={selectedLocation}
        label="Location"
        onChange={(e) => onLocationChange(e.target.value)}
        sx={{
          color: '#fff',
          '.MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
          '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.6)' },
          '.MuiSvgIcon-root': { color: '#fff' },
        }}
      >
        <MenuItem value="">All Locations</MenuItem>
        {(locations || []).map((loc) => (
          <MenuItem key={loc.location_id} value={loc.location_id}>
            {loc.location_id}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
