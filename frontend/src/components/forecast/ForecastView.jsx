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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import api from '../../api/axios';
import ForecastChart from '../dashboard/ForecastChart';

const ForecastView = () => {
  const [forecasts, setForecasts] = useState([]);
  const [selectedForecast, setSelectedForecast] = useState(null);
  const [modelType, setModelType] = useState('auto');
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeOutletId, setActiveOutletId] = useState(1);

  useEffect(() => {
    fetchForecasts();
  }, []);

  const fetchForecasts = async () => {
    try {
      // 1. Fetch stats first to get a valid outlet_id
      const statsRes = await api.get('/data/stats');
      const outletId = statsRes.data.suggested_outlet_id || 1;
      setActiveOutletId(outletId);

      const response = await api.get(`/forecast/history/${outletId}?limit=10`);
      setForecasts(response.data.forecasts);

      if (response.data.forecasts.length > 0) {
        fetchForecastDetails(response.data.forecasts[0].forecast_id);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching forecasts:', error);
      setLoading(false);
    }
  };

  const fetchForecastDetails = async (forecastId) => {
    try {
      const response = await api.get(`/forecast/${forecastId}`);
      setSelectedForecast(response.data);
    } catch (error) {
      console.error('Error fetching forecast details:', error);
    }
  };

  const handleGenerateForecast = async () => {
    setGenerating(true);

    try {
      await api.post('/forecast/generate', {
        outlet_id: activeOutletId,
        model_type: modelType,
        days_ahead: 7
      });

      fetchForecasts();
    } catch (error) {
      console.error('Error generating forecast:', error);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Forecasts
      </Typography>

      {/* Generate Forecast Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Generate New Forecast
        </Typography>

        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth>
              <InputLabel>Model Type</InputLabel>
              <Select
                value={modelType}
                label="Model Type"
                onChange={(e) => setModelType(e.target.value)}
              >
                <MenuItem value="auto">Auto Select (Best)</MenuItem>
                <MenuItem value="linear">Linear Regression</MenuItem>
                <MenuItem value="xgboost">XGBoost</MenuItem>
                <MenuItem value="arima">ARIMA</MenuItem>
                <MenuItem value="lstm">LSTM</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Button
              variant="contained"
              fullWidth
              startIcon={<Refresh />}
              onClick={handleGenerateForecast}
              disabled={generating}
            >
              {generating ? 'Generating...' : 'Generate Forecast'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Current Forecast Details */}
      {selectedForecast && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Forecast Details
          </Typography>

          <Box sx={{ mb: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Forecast Date
                </Typography>
                <Typography variant="h6">
                  {selectedForecast.forecast_date}
                </Typography>
              </Grid>

              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Predicted Customers
                </Typography>
                <Typography variant="h6">
                  {selectedForecast.predicted_customers}
                </Typography>
              </Grid>

              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Confidence Level
                </Typography>
                <Typography variant="h6">
                  {Math.round(selectedForecast.confidence_level * 100)}%
                </Typography>
              </Grid>
            </Grid>
          </Box>

          <Chip
            label={`Model: ${selectedForecast.model_used?.toUpperCase()}`}
            color="primary"
            sx={{ mr: 1 }}
          />
          <Chip
            label={`Created: ${new Date(selectedForecast.created_at).toLocaleString()}`}
            variant="outlined"
          />

          {/* Item Forecasts */}
          {selectedForecast.item_forecasts && Object.keys(selectedForecast.item_forecasts).length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Item-Level Predictions
              </Typography>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Item</strong></TableCell>
                      <TableCell align="right"><strong>Predicted Quantity</strong></TableCell>
                      <TableCell><strong>Category</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(selectedForecast.item_forecasts).map(([item, data]) => (
                      <TableRow key={item}>
                        <TableCell>{item}</TableCell>
                        <TableCell align="right">
                          {typeof data === 'object' ? data.predicted_quantity : data}
                        </TableCell>
                        <TableCell>{data.category || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Paper>
      )}

      {/* Forecast History */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Forecast History
        </Typography>

        {forecasts.length === 0 ? (
          <Alert severity="info">
            No forecasts available. Generate your first forecast above.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>ID</strong></TableCell>
                  <TableCell><strong>Date</strong></TableCell>
                  <TableCell align="right"><strong>Predicted Customers</strong></TableCell>
                  <TableCell><strong>Model</strong></TableCell>
                  <TableCell align="right"><strong>Confidence</strong></TableCell>
                  <TableCell><strong>Created</strong></TableCell>
                  <TableCell><strong>Action</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {forecasts.map((forecast) => (
                  <TableRow
                    key={forecast.forecast_id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => fetchForecastDetails(forecast.forecast_id)}
                  >
                    <TableCell>{forecast.forecast_id}</TableCell>
                    <TableCell>{forecast.forecast_date}</TableCell>
                    <TableCell align="right">{forecast.predicted_customers}</TableCell>
                    <TableCell>
                      <Chip
                        label={forecast.model_used?.toUpperCase()}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {Math.round(forecast.confidence_level * 100)}%
                    </TableCell>
                    <TableCell>
                      {new Date(forecast.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          fetchForecastDetails(forecast.forecast_id);
                        }}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
};

export default ForecastView;