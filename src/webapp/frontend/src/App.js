import React, { useState, useEffect } from 'react';
import {
  AppBar, Toolbar, Typography, Container,
  CssBaseline, Snackbar, Alert, ThemeProvider, createTheme,
} from '@mui/material';
import CloudIcon from '@mui/icons-material/Cloud';
import Dashboard from './components/Dashboard';
import LocationSelector from './components/LocationSelector';
import { fetchLocations } from './services/api';

const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    background: { default: '#f5f7fa' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: { borderRadius: 10 },
});

export default function App() {
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [error, setError] = useState('');

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
          <LocationSelector
            locations={locations}
            selectedLocation={selectedLocation}
            onLocationChange={setSelectedLocation}
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Dashboard selectedLocation={selectedLocation} />
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
