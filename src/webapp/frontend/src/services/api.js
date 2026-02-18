import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.message || error.message || 'Network error';
    return Promise.reject(new Error(message));
  }
);

export const fetchLocations = () => api.get('/locations');

export const fetchCurrentWeather = (locationId) => {
  const params = locationId ? { location_id: locationId } : {};
  return api.get('/weather/current', { params });
};

export const fetchHistorical = (locationId, start, end, page = 1, perPage = 20) => {
  const params = { page, per_page: perPage };
  if (locationId) params.location_id = locationId;
  if (start) params.start = start;
  if (end) params.end = end;
  return api.get('/weather/historical', { params });
};

export const fetchStats = (locationId, period = 'daily') => {
  const params = { period };
  if (locationId) params.location_id = locationId;
  return api.get('/weather/stats', { params });
};

export const fetchTrends = (locationId, days = 7) => {
  const params = { days };
  if (locationId) params.location_id = locationId;
  return api.get('/weather/trends', { params });
};

export const fetchCurrentAirQuality = (locationId) => {
  const params = locationId ? { location_id: locationId } : {};
  return api.get('/air-quality/current', { params });
};

export const fetchAirQualityHistorical = (locationId, start, end, page = 1, perPage = 20) => {
  const params = { page, per_page: perPage };
  if (locationId) params.location_id = locationId;
  if (start) params.start = start;
  if (end) params.end = end;
  return api.get('/air-quality/historical', { params });
};

export const fetchAirQualityStats = (locationId, period = 'daily') => {
  const params = { period };
  if (locationId) params.location_id = locationId;
  return api.get('/air-quality/stats', { params });
};

export const fetchAirQualityTrends = (locationId, days = 7) => {
  const params = { days };
  if (locationId) params.location_id = locationId;
  return api.get('/air-quality/trends', { params });
};
