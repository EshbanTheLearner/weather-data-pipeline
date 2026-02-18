import React, { useState, useEffect, useCallback } from 'react';
import {
  Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TablePagination, TextField, Button, Box,
  Skeleton, Stack,
} from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { fetchAirQualityHistorical } from '../services/api';
import { formatDateTime, daysAgo } from '../utils/dateFormatter';

export default function AirQualityHistorical({ locationId }) {
  const [rows, setRows] = useState([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [startDate, setStartDate] = useState(daysAgo(30));
  const [endDate, setEndDate] = useState(daysAgo(0));
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchAirQualityHistorical(
        locationId, startDate, endDate, page + 1, rowsPerPage
      );
      setRows(res.data || []);
      setTotal(res.pagination?.total || 0);
    } catch {
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [locationId, startDate, endDate, page, rowsPerPage]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleExportCsv = async () => {
    try {
      const res = await fetchAirQualityHistorical(locationId, startDate, endDate, 1, 10000);
      const data = res.data || [];
      if (data.length === 0) return;
      const headers = ['Timestamp', 'Location', 'AQI', 'Category', 'PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO'];
      const csvRows = [
        headers.join(','),
        ...data.map((r) =>
          [r.timestamp, r.location_id, r.aqi, r.aqi_category, r.pm25, r.pm10, r.o3, r.no2, r.so2, r.co].join(',')
        ),
      ];
      const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'air_quality_data.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently ignore export errors
    }
  };

  const columns = [
    { id: 'timestamp', label: 'Timestamp', format: formatDateTime },
    { id: 'location_id', label: 'Location' },
    { id: 'aqi', label: 'AQI' },
    { id: 'aqi_category', label: 'Category' },
    { id: 'pm25', label: 'PM2.5', format: (v) => v?.toFixed(1) },
    { id: 'pm10', label: 'PM10', format: (v) => v?.toFixed(1) },
    { id: 'o3', label: 'O3 (ppb)', format: (v) => v?.toFixed(1) },
    { id: 'no2', label: 'NO2 (ppb)', format: (v) => v?.toFixed(1) },
    { id: 'so2', label: 'SO2 (ppb)', format: (v) => v?.toFixed(1) },
    { id: 'co', label: 'CO (ppm)', format: (v) => v?.toFixed(2) },
  ];

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h6">Historical Air Quality Data</Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <TextField
            type="date"
            size="small"
            label="Start"
            value={startDate}
            onChange={(e) => { setStartDate(e.target.value); setPage(0); }}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            type="date"
            size="small"
            label="End"
            value={endDate}
            onChange={(e) => { setEndDate(e.target.value); setPage(0); }}
            InputLabelProps={{ shrink: true }}
          />
          <Button
            variant="outlined"
            size="small"
            startIcon={<FileDownloadIcon />}
            onClick={handleExportCsv}
          >
            CSV
          </Button>
        </Stack>
      </Box>

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.id} sx={{ fontWeight: 'bold' }}>
                  {col.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {columns.map((col) => (
                      <TableCell key={col.id}>
                        <Skeleton variant="text" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              : rows.map((row, idx) => (
                  <TableRow key={idx} hover>
                    {columns.map((col) => (
                      <TableCell key={col.id}>
                        {col.format ? col.format(row[col.id]) : row[col.id]}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
            {!loading && rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length} align="center">
                  No data available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={total}
        page={page}
        onPageChange={(_, p) => setPage(p)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(e) => {
          setRowsPerPage(parseInt(e.target.value, 10));
          setPage(0);
        }}
        rowsPerPageOptions={[10, 20, 50]}
      />
    </Paper>
  );
}
