import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert,
  CircularProgress,
  Stack,
  Fade,
  alpha
} from '@mui/material';
import {
  PictureAsPdf,
  TableChart,
  Assessment,
  Summarize,
  Inventory2,
  FileDownload
} from '@mui/icons-material';
import api from '../../api/axios';

const ReportsPage = () => {
  const [forecasts, setForecasts] = useState([]);
  const [selectedForecast, setSelectedForecast] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchForecasts();
  }, []);

  const fetchForecasts = async () => {
    try {
      const statsRes = await api.get('/data/stats');
      const outletId = statsRes.data.suggested_outlet_id || 1;

      const response = await api.get(`/forecast/history/${outletId}?limit=10`);
      setForecasts(response.data.forecasts);
      if (response.data.forecasts.length > 0) {
        setSelectedForecast(response.data.forecasts[0].forecast_id);
      }
    } catch (error) {
      console.error('Error fetching forecasts:', error);
    }
  };

  const downloadFile = async (url, filename) => {
    setLoading(true);
    setMessage('');
    try {
      const response = await api.get(url, { responseType: 'blob' });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setMessage(`Successfully downloaded ${filename}`);
    } catch (error) {
      setMessage(`Error downloading ${filename}`);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadForecastReport = () =>
    downloadFile(`/reports/forecast/${selectedForecast}`, `forecast_report_${selectedForecast}.pdf`);

  const handleDownloadInventoryReport = () =>
    downloadFile(`/reports/inventory/${selectedForecast}`, `inventory_report_${selectedForecast}.pdf`);

  const handleDownloadExcelReport = () =>
    downloadFile(`/reports/forecast/${selectedForecast}?format=excel`, `forecast_report_${selectedForecast}.xlsx`);

  return (
    <Fade in={true} timeout={800}>
      <Box sx={{ pb: 6 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: '-1px', mb: 0.5 }}>
            Reports & Intelligence
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Export comprehensive data and analytics for your stakeholders.
          </Typography>
        </Box>

        {message && (
          <Alert
            severity={message.includes('Error') ? 'error' : 'success'}
            variant="filled"
            sx={{ mb: 4, borderRadius: 3 }}
            onClose={() => setMessage('')}
          >
            {message}
          </Alert>
        )}

        <Grid container spacing={4}>
          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 4, borderRadius: 4, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <Summarize sx={{ color: '#6366f1' }} />
                <Typography variant="h6" sx={{ fontWeight: 700 }}>Configuration</Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Select a specific forecast execution to generate associated reports.
              </Typography>

              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Target Forecast</InputLabel>
                <Select
                  value={selectedForecast}
                  label="Target Forecast"
                  onChange={(e) => setSelectedForecast(e.target.value)}
                  sx={{ borderRadius: 3 }}
                >
                  {forecasts.map((f) => (
                    <MenuItem key={f.forecast_id} value={f.forecast_id}>
                      Forecast #{f.forecast_id} ({f.forecast_date})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {selectedForecast && (
                <Box sx={{ p: 2, bgcolor: '#f8fafc', borderRadius: 3 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: 'block', mb: 1 }}>
                    SELECTED RUN SUMMARY
                  </Typography>
                  {forecasts.filter(f => f.forecast_id === selectedForecast).map(f => (
                    <Stack spacing={1} key={f.forecast_id}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Predicted Orders</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>{f.predicted_customers}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Confidence</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>{Math.round(f.confidence_level * 100)}%</Typography>
                      </Box>
                    </Stack>
                  ))}
                </Box>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 4, borderRadius: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 4 }}>
                <FileDownload sx={{ color: '#6366f1' }} />
                <Typography variant="h6" sx={{ fontWeight: 700 }}>Download Center</Typography>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Box sx={{ p: 3, border: '1px solid #f1f5f9', borderRadius: 4, bgcolor: 'rgba(99, 102, 241, 0.02)' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                      <Assessment sx={{ color: '#6366f1' }} />
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Demand Intelligence</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      Detailed PDF report including charts, item-level predictions, and model diagnostics.
                    </Typography>
                    <Button
                      fullWidth
                      variant="contained"
                      onClick={handleDownloadForecastReport}
                      disabled={loading || !selectedForecast}
                    >
                      {loading ? <CircularProgress size={20} color="inherit" /> : 'Download Analysis PDF'}
                    </Button>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Box sx={{ p: 3, border: '1px solid #f1f5f9', borderRadius: 4, bgcolor: 'rgba(16, 185, 129, 0.02)' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                      <Inventory2 sx={{ color: '#10b981' }} />
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Procurement Plan</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      PDF report with full shopping list, estimated budget, and supplier purchase orders.
                    </Typography>
                    <Button
                      fullWidth
                      variant="contained"
                      color="success"
                      onClick={handleDownloadInventoryReport}
                      disabled={loading || !selectedForecast}
                      sx={{ bgcolor: '#10b981' }}
                    >
                      {loading ? <CircularProgress size={20} color="inherit" /> : 'Download Inventory PDF'}
                    </Button>
                  </Box>
                </Grid>

                <Grid item xs={12}>
                  <Box sx={{ p: 3, border: '1px solid #f1f5f9', borderRadius: 4, display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: 'center', gap: 3 }}>
                    <TableChart sx={{ color: '#64748b', fontSize: 40 }} />
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Excel Export (Raw Data)</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Perfect for manual auditing or importing into other systems.
                      </Typography>
                    </Box>
                    <Button
                      variant="outlined"
                      onClick={handleDownloadExcelReport}
                      disabled={loading || !selectedForecast}
                      sx={{ minWidth: 200 }}
                    >
                      Export to .XLSX
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
};

export default ReportsPage;
