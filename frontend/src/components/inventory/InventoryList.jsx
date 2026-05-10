import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  Grid,
  Stack,
  Fade,
  Avatar,
  alpha
} from '@mui/material';
import { 
  Download, 
  Inventory, 
  Payments, 
  Numbers, 
  LocalShipping,
  ReceiptLong,
  ShoppingCart
} from '@mui/icons-material';
import api from '../../api/axios';

const InventoryList = () => {
  const [inventory, setInventory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [latestForecastId, setLatestForecastId] = useState(null);

  useEffect(() => {
    fetchLatestForecast();
  }, []);

  const fetchLatestForecast = async () => {
    try {
      const statsRes = await api.get('/data/stats');
      const outletId = statsRes.data.suggested_outlet_id || 1;

      const response = await api.get(`/forecast/latest/${outletId}`);
      setLatestForecastId(response.data.forecast_id);
      fetchInventorySuggestions(response.data.forecast_id);
    } catch (error) {
      console.error('Error fetching latest forecast:', error);
    }
  };

  const fetchInventorySuggestions = async (forecastId) => {
    setLoading(true);
    try {
      const response = await api.get(`/inventory/suggestions/${forecastId}`);
      setInventory(response.data);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!latestForecastId) return;

    setLoading(true);
    try {
      const response = await api.get(
        `/reports/inventory/${latestForecastId}`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `inventory_report_${latestForecastId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !inventory) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <Inventory sx={{ fontSize: 40, color: '#94a3b8', mb: 2 }} />
        <Typography variant="body1" color="text.secondary">Loading inventory suggestions...</Typography>
      </Box>
    );
  }

  if (!inventory && !loading) {
    return (
      <Fade in={true}>
        <Box sx={{ p: 4 }}>
          <Alert severity="info" sx={{ borderRadius: 3 }}>
            No inventory data available. Generate a forecast first.
          </Alert>
        </Box>
      </Fade>
    );
  }

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <Paper sx={{ p: 3, borderRadius: 4, height: '100%', display: 'flex', alignItems: 'center', gap: 2.5 }}>
      <Avatar sx={{ bgcolor: alpha(color, 0.1), color: color, width: 56, height: 56 }}>
        <Icon />
      </Avatar>
      <Box>
        <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {title}
        </Typography>
        <Typography variant="h5" sx={{ fontWeight: 800, color: '#1e293b' }}>
          {value}
        </Typography>
      </Box>
    </Paper>
  );

  return (
    <Fade in={true} timeout={800}>
      <Box sx={{ pb: 6 }}>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between', 
          alignItems: { xs: 'flex-start', sm: 'center' }, 
          mb: 4,
          gap: 2
        }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: '-1px', mb: 0.5 }}>
              Inventory Planning
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Strategic procurement based on predicted demand.
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={handleExport}
            disabled={loading || !latestForecastId}
            sx={{ 
              backgroundColor: '#10b981', 
              '&:hover': { backgroundColor: '#059669' },
              borderRadius: '10px',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.2)'
            }}
          >
            {loading ? 'Exporting...' : 'Export PDF Report'}
          </Button>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={4}>
            <StatCard 
              title="Requirements" 
              value={inventory.shopping_list?.total_items || 0} 
              icon={Numbers} 
              color="#6366f1"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <StatCard 
              title="Estimated Budget" 
              value={`$${inventory.shopping_list?.total_cost?.toLocaleString() || '0.00'}`} 
              icon={Payments} 
              color="#10b981"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <StatCard 
              title="Active Forecast" 
              value={`#${latestForecastId}`} 
              icon={ReceiptLong} 
              color="#f59e0b"
            />
          </Grid>
        </Grid>

        <Grid container spacing={4}>
          <Grid item xs={12} lg={7}>
            <Paper sx={{ p: 3, borderRadius: 4 }}>
              <Typography variant="h6" sx={{ mb: 3, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                <ShoppingCart sx={{ color: '#6366f1' }} /> Detailed Shopping List
              </Typography>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: '#f8fafc' }}>
                      <TableCell sx={{ fontWeight: 700, color: '#64748b' }}>Ingredient</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700, color: '#64748b' }}>Quantity</TableCell>
                      <TableCell sx={{ fontWeight: 700, color: '#64748b' }}>Unit</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700, color: '#64748b' }}>Est. Cost</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {inventory.shopping_list?.items?.map((item, index) => (
                      <TableRow key={index} sx={{ '&:hover': { bgcolor: '#f1f5f9' } }}>
                        <TableCell sx={{ fontWeight: 500 }}>{item.ingredient}</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600 }}>{item.quantity}</TableCell>
                        <TableCell><Chip label={item.unit} size="small" variant="outlined" /></TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600, color: '#10b981' }}>
                          ${item.cost?.toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} lg={5}>
            {inventory.purchase_orders && Object.keys(inventory.purchase_orders).length > 0 && (
              <Box>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LocalShipping sx={{ color: '#f59e0b' }} /> Logistics & Suppliers
                </Typography>

                {Object.entries(inventory.purchase_orders).map(([supplier, order], idx) => (
                  <Paper key={supplier} sx={{ p: 3, mb: 3, borderRadius: 4, border: '1px solid #e2e8f0' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {supplier}
                      </Typography>
                      <Typography variant="subtitle2" sx={{ color: '#10b981', fontWeight: 800 }}>
                        ${order.total_cost?.toFixed(2) || '0.00'}
                      </Typography>
                    </Box>

                    <Stack spacing={1.5}>
                      {order.items?.map((item, i) => (
                        <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1.5, bgcolor: '#f8fafc', borderRadius: 2 }}>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>{item.ingredient}</Typography>
                          <Typography variant="caption" sx={{ color: '#64748b' }}>
                            {item.quantity} {item.unit}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  </Paper>
                ))}
              </Box>
            )}
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
};

export default InventoryList;