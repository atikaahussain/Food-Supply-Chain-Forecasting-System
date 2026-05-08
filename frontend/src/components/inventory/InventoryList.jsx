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
  Grid
} from '@mui/material';
import { ShoppingCart, Download } from '@mui/icons-material';
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
      // 1. Fetch stats first to get a valid outlet_id
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
      setLoading(false);
    } catch (error) {
      console.error('Error fetching inventory:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <Typography>Loading inventory suggestions...</Typography>;
  }

  if (!inventory) {
    return (
      <Alert severity="info">
        No inventory data available. Generate a forecast first.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">
          Inventory Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Download />}
          color="success"
        >
          Export Shopping List
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography color="text.secondary" variant="body2">
              Total Items
            </Typography>
            <Typography variant="h4">
              {inventory.shopping_list?.total_items || 0}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography color="text.secondary" variant="body2">
              Total Cost
            </Typography>
            <Typography variant="h4">
              ${inventory.shopping_list?.total_cost?.toFixed(2) || '0.00'}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography color="text.secondary" variant="body2">
              Forecast ID
            </Typography>
            <Typography variant="h4">
              #{latestForecastId}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Shopping List */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Shopping List
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Ingredient</strong></TableCell>
                <TableCell align="right"><strong>Quantity</strong></TableCell>
                <TableCell><strong>Unit</strong></TableCell>
                <TableCell align="right"><strong>Cost</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {inventory.shopping_list?.items?.map((item, index) => (
                <TableRow key={index}>
                  <TableCell>{item.ingredient}</TableCell>
                  <TableCell align="right">{item.quantity}</TableCell>
                  <TableCell>{item.unit}</TableCell>
                  <TableCell align="right">${item.cost?.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Purchase Orders by Supplier */}
      {inventory.purchase_orders && Object.keys(inventory.purchase_orders).length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Purchase Orders by Supplier
          </Typography>

          {Object.entries(inventory.purchase_orders).map(([supplier, order]) => (
            <Box key={supplier} sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle1">
                  {supplier}
                </Typography>
                <Chip
                  label={`Total: $${order.total_cost?.toFixed(2) || '0.00'}`}
                  color="primary"
                />
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Ingredient</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell>Unit</TableCell>
                      <TableCell align="right">Unit Price</TableCell>
                      <TableCell align="right">Total</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {order.items?.map((item, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{item.ingredient}</TableCell>
                        <TableCell align="right">{item.quantity}</TableCell>
                        <TableCell>{item.unit}</TableCell>
                        <TableCell align="right">
                          ${item.unit_price?.toFixed(2) || '0.00'}
                        </TableCell>
                        <TableCell align="right">
                          ${item.line_total?.toFixed(2) || '0.00'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          ))}
        </Paper>
      )}
    </Box>
  );
};

export default InventoryList;