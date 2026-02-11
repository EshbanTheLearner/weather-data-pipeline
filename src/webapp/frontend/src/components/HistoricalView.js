import React, { useState, useEffect, useCallback } from 'react';
import {
  Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TablePagination, TextField, Button, Box,
  Skeleton, Stack,
} from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { fetchHistorical } from '../services/api';
import { formatDateTime, daysAgo } from '../utils/dateFormatter';
import { convertTemp, tempUnit } from '../utils/temperatureUtils';

export default function HistoricalView({ locationId, temperatureUnit }) {
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
      const res = await fetchHistorical(
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
      const res = await fetchHistorical(locationId, startDate, endDate, 1, 10000);
      const data = res.data || [];
      if (data.length === 0) return;
      const headers = ['Timestamp', 'Location', 'Temperature (C)', 'Humidity (%)', 'Pressure (hPa)', 'Wind Speed (m/s)'];
      const csvRows = [
        headers.join(','),
        ...data.map((r) =>
          [r.timestamp, r.location_id, r.temperature, r.humidity, r.pressure, r.wind_speed].join(',')
        ),
      ];
      const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'weather_data.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently ignore export errors
    }
  };

  const columns = [
    { id: 'timestamp', label: 'Timestamp', format: formatDateTime },
    { id: 'location_id', label: 'Location' },
    { id: 'temperature', label: `Temp (${tempUnit(temperatureUnit)})`, format: (v) => convertTemp(v, temperatureUnit)?.toFixed(1) },
    { id: 'humidity', label: 'Humidity (%)', format: (v) => v?.toFixed(1) },
    { id: 'pressure', label: 'Pressure (hPa)', format: (v) => v?.toFixed(0) },
    { id: 'wind_speed', label: 'Wind (m/s)', format: (v) => v?.toFixed(1) },
  ];

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h6">Historical Weather Data</Typography>
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
