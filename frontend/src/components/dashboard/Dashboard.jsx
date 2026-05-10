import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Typography,
  Paper,
  Alert,
  Button,
  Chip,
  CircularProgress,
  Stack,
  Fade,
  useTheme
} from '@mui/material';
import {
  People,
  TrendingUp,
  Warning,
  Refresh,
  Storage,
  AutoGraph,
  CalendarMonth,
  Restaurant
} from '@mui/icons-material';
import MetricCard from './MetricCard';
import ForecastChart from './ForecastChart';
import AlertsPanel from '../inventory/AlertsPanel';
import api from '../../api/axios';

const Dashboard = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [latestForecast, setLatestForecast] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [dbStats, setDbStats] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [activeOutletId, setActiveOutletId] = useState(1);
  const [chartData, setChartData] = useState([]);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const statsRes = await api.get('/data/stats');
      const stats = statsRes.data;
      setDbStats(stats);

      const outletId = stats.suggested_outlet_id || 1;
      setActiveOutletId(outletId);

      const [forecastRes, alertsRes, chartRes] = await Promise.allSettled([
        api.get(`/forecast/latest/${outletId}`),
        api.get(`/inventory/alerts/${outletId}`),
        api.get(`/forecast/chart-data/${outletId}`),
      ]);

      if (forecastRes.status === 'fulfilled') {
        setLatestForecast(forecastRes.value.data);
      } else {
        setLatestForecast(null);
      }

      if (alertsRes.status === 'fulfilled') {
        setAlerts(alertsRes.value.data.alerts || []);
      }

      if (chartRes.status === 'fulfilled') {
        setChartData(chartRes.value.data);
      }
    } catch (err) {
      setError('Could not reach the backend. Ensure the Flask server is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleGenerateForecast = async () => {
    setGenerating(true);
    try {
      await api.post('/forecast/generate', {
        outlet_id: activeOutletId,
        model_type: 'auto',
        days_ahead: 7,
      });
      fetchDashboardData();
    } catch (err) {
      const msg = err.response?.data?.error || err.message;
      setError(`Forecast generation failed: ${msg}`);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress thickness={4} size={50} sx={{ mb: 2, color: theme.palette.primary.main }} />
        <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 500 }}>
          Synthesizing your data...
        </Typography>
      </Box>
    );
  }

  return (
    <Fade in={true} timeout={800}>
      <Box sx={{ pb: 6 }}>
        {/* Header Section */}
        <Box sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', md: 'center' },
          mb: 5,
          gap: 2
        }}>
          <Box>
            <Typography variant="h4" sx={{ mb: 0.5, letterSpacing: '-1px' }}>
              System Overview
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Real-time analytics and predictive forecasting for your kitchen.
            </Typography>
          </Box>
          <Stack direction="row" spacing={1.5} sx={{ width: { xs: '100%', md: 'auto' } }}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchDashboardData}
              disabled={loading}
              sx={{ flex: { xs: 1, md: 'none' }, borderColor: '#e2e8f0', color: '#64748b' }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AutoGraph />}
              onClick={handleGenerateForecast}
              disabled={generating}
              sx={{
                flex: { xs: 1, md: 'none' },
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
              }}
            >
              {generating ? 'Processing…' : 'Generate Forecast'}
            </Button>
          </Stack>
        </Box>

        {/* Error Notification */}
        {error && (
          <Alert severity="error" variant="filled" sx={{ mb: 4, borderRadius: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Top Metric Cards */}
        <Grid container spacing={3} sx={{ mb: 5 }}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Predicted Orders"
              value={latestForecast?.predicted_customers ?? '0'}
              icon={People}
              color="#6366f1"
              trend="+12%"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Data Integrity"
              value={dbStats?.total_records ? `${(dbStats.total_records / 1000).toFixed(1)}k` : '0'}
              icon={Storage}
              color="#10b981"
              trend="Stable"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Model Accuracy"
              value={latestForecast?.confidence_level ? `${Math.round(latestForecast.confidence_level * 100)}%` : '—'}
              icon={TrendingUp}
              color="#f59e0b"
              trend="High"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="System Alerts"
              value={alerts.length}
              icon={Warning}
              color={alerts.length > 0 ? "#ef4444" : "#10b981"}
              trend={alerts.length > 0 ? "Action Required" : "All Good"}
            />
          </Grid>
        </Grid>

        <Grid container spacing={4}>
          {/* Main Chart Area */}
          <Grid item xs={12} lg={8}>
            {latestForecast ? (
              <Box sx={{ mb: 4 }}>
                <ForecastChart
                  data={chartData}
                  title="Demand Prediction Analysis"
                />
              </Box>
            ) : (
              <Paper sx={{
                p: 6,
                textAlign: 'center',
                borderRadius: 4,
                backgroundColor: 'rgba(99, 102, 241, 0.02)',
                border: '2px dashed #e2e8f0'
              }}>
                <CalendarMonth sx={{ fontSize: 60, color: '#94a3b8', mb: 2 }} />
                <Typography variant="h6" color="text.primary" gutterBottom>
                  Ready for Prediction
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 400, mx: 'auto' }}>
                  We need a bit more data or a fresh generation to show your sales trends and predictions.
                </Typography>
                <Button variant="contained" onClick={handleGenerateForecast} disabled={generating}>
                  Initialize Your First Forecast
                </Button>
              </Paper>
            )}

            {/* Quick Stats Summary */}
            {dbStats && (
              <Paper sx={{ p: 3, borderRadius: 4, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                <Typography variant="subtitle2" sx={{ color: '#64748b', mr: 2 }}>DATA SNAPSHOT:</Typography>
                <Chip icon={<Restaurant sx={{ fontSize: '1rem !important' }} />} label={`Meals: ${dbStats.total_food_items}`} sx={{ fontWeight: 600 }} />
                <Chip label={`Location ID: ${activeOutletId}`} variant="outlined" sx={{ fontWeight: 600 }} />
                {dbStats.date_range?.min && (
                  <Chip
                    label={`${dbStats.date_range.min} to ${dbStats.date_range.max}`}
                    sx={{ backgroundColor: '#f1f5f9', fontWeight: 500 }}
                  />
                )}
              </Paper>
            )}
          </Grid>

          {/* Sidebar Area (Alerts & Activity) */}
          <Grid item xs={12} lg={4}>
            <AlertsPanel outletId={activeOutletId} />

            {latestForecast && (
              <Paper sx={{ p: 3, mt: 4, borderRadius: 4, background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)' }}>
                <Typography variant="h6" sx={{ mb: 2, fontSize: '1.1rem' }}>Latest Run Details</Typography>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Execution Date</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{latestForecast.forecast_date}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Algorithm</Typography>
                    <Chip size="small" label={latestForecast.model_used?.toUpperCase() || 'AUTO'} sx={{ fontWeight: 700, height: 20, fontSize: '0.65rem' }} />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Target Window</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>Next 7 Days</Typography>
                  </Box>
                </Stack>
              </Paper>
            )}
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
};

export default Dashboard;
