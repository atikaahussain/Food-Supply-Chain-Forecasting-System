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
  Alert,
  Stack,
  Fade,
  LinearProgress,
  IconButton,
  Tooltip,
  alpha
} from '@mui/material';
import { Refresh, Timeline, Analytics, History, Visibility, AutoGraph } from '@mui/icons-material';
import api from '../../api/axios';

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
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <LinearProgress sx={{ borderRadius: 2, height: 6 }} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Loading intelligence data...</Typography>
      </Box>
    );
  }

  return (
    <Fade in={true} timeout={800}>
      <Box sx={{ pb: 6 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: '-1px', mb: 0.5 }}>
            Predictive Intelligence
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Advanced demand modeling and item-level distribution.
          </Typography>
        </Box>

        <Grid container spacing={4}>
          <Grid item xs={12} lg={4}>
            {/* Generate Section */}
            <Paper sx={{ p: 4, borderRadius: 4, mb: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <AutoGraph sx={{ color: '#6366f1' }} />
                <Typography variant="h6" sx={{ fontWeight: 700 }}>Model Configuration</Typography>
              </Box>

              <Stack spacing={3}>
                <FormControl fullWidth>
                  <InputLabel>Target Algorithm</InputLabel>
                  <Select
                    value={modelType}
                    label="Target Algorithm"
                    onChange={(e) => setModelType(e.target.value)}
                    sx={{ borderRadius: 3 }}
                  >
                    <MenuItem value="auto">Auto Select (Best Fit)</MenuItem>
                    <MenuItem value="linear">Linear Regression</MenuItem>
                    <MenuItem value="xgboost">XGBoost Optimized</MenuItem>
                    <MenuItem value="arima">ARIMA (Time Series)</MenuItem>
                    <MenuItem value="lstm">LSTM (Deep Learning)</MenuItem>
                  </Select>
                </FormControl>

                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<Refresh />}
                  onClick={handleGenerateForecast}
                  disabled={generating}
                  sx={{ py: 1.5 }}
                >
                  {generating ? 'Processing Model...' : 'Execute Forecast'}
                </Button>
              </Stack>
            </Paper>

            {/* History List */}
            <Paper sx={{ p: 4, borderRadius: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <History sx={{ color: '#64748b' }} />
                <Typography variant="h6" sx={{ fontWeight: 700 }}>Execution History</Typography>
              </Box>

              {forecasts.length === 0 ? (
                <Alert severity="info" sx={{ borderRadius: 3 }}>No history found.</Alert>
              ) : (
                <Stack spacing={1}>
                  {forecasts.map((f) => {
                    const isActive = selectedForecast?.forecast_id === f.forecast_id;
                    return (
                      <Box
                        key={f.forecast_id}
                        onClick={() => fetchForecastDetails(f.forecast_id)}
                        sx={{
                          p: 2,
                          borderRadius: 3,
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          border: '1px solid',
                          borderColor: isActive ? '#6366f1' : '#f1f5f9',
                          bgcolor: isActive ? alpha('#6366f1', 0.05) : 'transparent',
                          '&:hover': { bgcolor: '#f8fafc' }
                        }}
                      >
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>#{f.forecast_id}</Typography>
                          <Typography variant="caption" color="text.secondary">{f.forecast_date}</Typography>
                        </Box>
                        <Tooltip title="View Details">
                          <IconButton size="small"><Visibility sx={{ fontSize: 18 }} /></IconButton>
                        </Tooltip>
                      </Box>
                    );
                  })}
                </Stack>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} lg={8}>
            {selectedForecast ? (
              <Box>
                <Paper sx={{ p: 4, borderRadius: 4, mb: 4, background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)', color: 'white' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
                    <Box>
                      <Typography variant="caption" sx={{ opacity: 0.8, fontWeight: 600, letterSpacing: '1px' }}>SELECTED RUN DETAILS</Typography>
                      <Typography variant="h3" sx={{ fontWeight: 800, letterSpacing: '-1px' }}>#{selectedForecast.forecast_id}</Typography>
                    </Box>
                    <Chip
                      label={selectedForecast.model_used?.toUpperCase()}
                      sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 700, borderRadius: 2 }}
                    />
                  </Box>

                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" sx={{ opacity: 0.8 }}>PREDICTED CUSTOMERS</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700 }}>{selectedForecast.predicted_customers}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" sx={{ opacity: 0.8 }}>CONFIDENCE LEVEL</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700 }}>{Math.round(selectedForecast.confidence_level * 100)}%</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" sx={{ opacity: 0.8 }}>EXECUTION DATE</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 700 }}>{selectedForecast.forecast_date}</Typography>
                    </Grid>
                  </Grid>
                </Paper>

                {/* Item Distribution */}
                <Paper sx={{ p: 4, borderRadius: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 4 }}>
                    <Analytics sx={{ color: '#6366f1' }} />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>Item Distribution Model</Typography>
                  </Box>

                  {selectedForecast.item_forecasts && Object.keys(selectedForecast.item_forecasts).length > 0 ? (
                    <TableContainer>
                      <Table>
                        <TableHead>
                          <TableRow sx={{ bgcolor: '#f8fafc' }}>
                            <TableCell sx={{ fontWeight: 700, color: '#64748b' }}>Item Name</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 700, color: '#64748b' }}>Predicted Demand</TableCell>
                            <TableCell sx={{ fontWeight: 700, color: '#64748b' }}>Category</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {Object.entries(selectedForecast.item_forecasts).map(([item, data]) => (
                            <TableRow key={item} sx={{ '&:hover': { bgcolor: '#f1f5f9' } }}>
                              <TableCell sx={{ fontWeight: 600 }}>{item}</TableCell>
                              <TableCell align="right" sx={{ fontWeight: 700, color: '#6366f1' }}>
                                {typeof data === 'object' ? data.predicted_quantity : data}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={data.category || 'Standard'}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontSize: '0.65rem', height: 20 }}
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Box sx={{ p: 4, textAlign: 'center' }}>
                      <Typography color="text.secondary">No item-level data found for this run.</Typography>
                    </Box>
                  )}
                </Paper>
              </Box>
            ) : (
              <Paper sx={{ p: 6, textAlign: 'center', borderRadius: 4, border: '2px dashed #e2e8f0' }}>
                <Timeline sx={{ fontSize: 60, color: '#94a3b8', mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 700 }}>No Run Selected</Typography>
                <Typography variant="body2" color="text.secondary">Select an execution from the history to view detailed intelligence.</Typography>
              </Paper>
            )}
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
};

export default ForecastView;