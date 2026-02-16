import React, { useState, useEffect, useMemo } from 'react';
import {
  AppBar, Toolbar, Typography, Container,
  CssBaseline, Snackbar, Alert, ThemeProvider, createTheme,
  ToggleButtonGroup, ToggleButton, IconButton, Tooltip,
} from '@mui/material';
import CloudIcon from '@mui/icons-material/Cloud';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import Dashboard from './components/Dashboard';
import LocationSelector from './components/LocationSelector';
import { fetchLocations } from './services/api';

export default function App() {
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [temperatureUnit, setTemperatureUnit] = useState('C');
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem('weatherDashboardDarkMode') === 'true'
  );

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: darkMode ? 'dark' : 'light',
          primary: { main: '#1976d2' },
          ...(darkMode ? {} : { background: { default: '#f5f7fa' } }),
        },
        typography: {
          fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        },
        shape: { borderRadius: 10 },
      }),
    [darkMode]
  );

  const handleDarkModeToggle = () => {
    setDarkMode((prev) => {
      const next = !prev;
      localStorage.setItem('weatherDashboardDarkMode', String(next));
      return next;
    });
  };

  useEffect(() => {
    fetchLocations()
      .then((res) => setLocations(res.data || []))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      <AppBar position="static" elevation={1}>
        <Toolbar>
          <CloudIcon sx={{ mr: 1.5 }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
            Weather Dashboard
          </Typography>
          <ToggleButtonGroup
            value={temperatureUnit}
            exclusive
            onChange={(_, v) => { if (v) setTemperatureUnit(v); }}
            size="small"
            sx={{ mr: 2, bgcolor: 'rgba(255,255,255,0.15)', '& .MuiToggleButton-root': { color: 'rgba(255,255,255,0.7)', '&.Mui-selected': { color: '#fff', bgcolor: 'rgba(255,255,255,0.25)' } } }}
          >
            <ToggleButton value="C">°C</ToggleButton>
            <ToggleButton value="F">°F</ToggleButton>
          </ToggleButtonGroup>
          <Tooltip title={darkMode ? 'Light mode' : 'Dark mode'}>
            <IconButton color="inherit" onClick={handleDarkModeToggle} sx={{ mr: 1 }}>
              {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
          </Tooltip>
          <LocationSelector
            locations={locations}
            selectedLocation={selectedLocation}
            onLocationChange={setSelectedLocation}
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Dashboard selectedLocation={selectedLocation} temperatureUnit={temperatureUnit} />
      </Container>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setError('')} variant="filled">
          {error}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
}
