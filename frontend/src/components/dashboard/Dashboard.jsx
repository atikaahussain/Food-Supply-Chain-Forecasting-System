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
} from '@mui/material';
import {
  People,
  TrendingUp,
  Warning,
  Refresh,
  Storage,
} from '@mui/icons-material';
import MetricCard from './MetricCard';
import ForecastChart from './ForecastChart';
import AlertsPanel from '../inventory/AlertsPanel';
import api from '../../api/axios';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [latestForecast, setLatestForecast] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [dbStats, setDbStats] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [activeOutletId, setActiveOutletId] = useState(1);
  const [chartData, setChartData] = useState([]);

  // ── Fetch all dashboard data ──────────────────────────────────────────────
  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Fetch stats first to get a valid outlet_id
      const statsRes = await api.get('/data/stats');
      const stats = statsRes.data;
      setDbStats(stats);

      const outletId = stats.suggested_outlet_id || 1;
      setActiveOutletId(outletId);

      // 2. Fetch other data using the valid outlet_id
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

      // Surface an error only if stats failed
    } catch (err) {
      setError('Could not reach the backend. Is the Flask server running on port 5000?');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // ── Generate forecast ─────────────────────────────────────────────────────
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

  // ── Loading state ─────────────────────────────────────────────────────────
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 8 }}>
        <CircularProgress sx={{ mr: 2 }} />
        <Typography>Loading dashboard…</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchDashboardData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleGenerateForecast}
            disabled={generating}
          >
            {generating ? 'Generating…' : 'Generate New Forecast'}
          </Button>
        </Box>
      </Box>

      {/* Error banner */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Metric cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Predicted Customers"
            value={latestForecast?.predicted_customers ?? '—'}
            change={null}
            icon={People}
            color="primary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Sales Records"
            value={dbStats?.total_records?.toLocaleString() ?? '—'}
            change={null}
            icon={Storage}
            color="success"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Forecast Confidence"
            value={
              latestForecast?.confidence_level != null
                ? `${Math.round(latestForecast.confidence_level * 100)}%`
                : '—'
            }
            change={null}
            icon={TrendingUp}
            color="info"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Alerts"
            value={alerts.length}
            icon={Warning}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* DB Stats strip */}
      {dbStats && (
        <Paper sx={{ p: 2, mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip label={`Food Items: ${dbStats.total_food_items}`} variant="outlined" />
          <Chip label={`Outlets: ${dbStats.total_outlets}`} variant="outlined" />
          {dbStats.date_range?.min && (
            <Chip
              label={`Data: ${dbStats.date_range.min} → ${dbStats.date_range.max}`}
              variant="outlined"
            />
          )}
          {!dbStats.has_data && (
            <Chip label="No sales data uploaded yet" color="warning" />
          )}
        </Paper>
      )}

      {/* Latest forecast summary */}
      {latestForecast && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Latest Forecast
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              label={`Date: ${latestForecast.forecast_date}`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`Model: ${latestForecast.model_used?.toUpperCase()}`}
              color="secondary"
              variant="outlined"
            />
            <Chip
              label={`Confidence: ${Math.round(latestForecast.confidence_level * 100)}%`}
              color="success"
              variant="outlined"
            />
          </Box>
        </Paper>
      )}

      <Grid item xs={12}>
        <AlertsPanel outletId={activeOutletId} />
      </Grid>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Box sx={{ mb: 3 }}>
          {alerts.slice(0, 3).map((alert, index) => (
            <Alert
              key={index}
              severity={alert.severity === 'high' ? 'error' : 'warning'}
              sx={{ mb: 1 }}
            >
              <strong>{alert.ingredient}:</strong> {alert.message}
            </Alert>
          ))}
        </Box>
      )}

      {/* Chart — only shown when there is real forecast data */}
      {latestForecast ? (
        <ForecastChart
          data={chartData}
          title="Customer Count: Actual vs Predicted"
        />
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Forecast Data Yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload sales data via the <strong>Upload</strong> page, then click{' '}
            <strong>Generate New Forecast</strong> to populate this dashboard.
          </Typography>
          <Button variant="contained" onClick={handleGenerateForecast} disabled={generating}>
            {generating ? 'Generating…' : 'Generate First Forecast'}
          </Button>
        </Paper>
      )}
    </Box>
  );
};

export default Dashboard;
