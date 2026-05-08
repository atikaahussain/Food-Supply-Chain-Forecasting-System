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
  TextField,
  Divider,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  PictureAsPdf,
  Email,
  TableChart,
  Assessment
} from '@mui/icons-material';
import api from '../../api/axios';

const ReportsPage = () => {
  const [forecasts, setForecasts] = useState([]);
  const [selectedForecast, setSelectedForecast] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchForecasts();
  }, []);

  const fetchForecasts = async () => {
    try {
      // Fetch stats first to get a valid outlet_id
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

  const handleDownloadForecastReport = async () => {
    if (!selectedForecast) {
      setMessage('Please select a forecast');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await api.get(
        `/reports/forecast/${selectedForecast}`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `forecast_report_${selectedForecast}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage('Report downloaded successfully!');
    } catch (error) {
      setMessage('Error downloading report');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadInventoryReport = async () => {
    if (!selectedForecast) {
      setMessage('Please select a forecast');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await api.get(
        `/reports/inventory/${selectedForecast}`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `inventory_report_${selectedForecast}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage('Inventory report downloaded successfully!');
    } catch (error) {
      setMessage('Error downloading inventory report');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadExcelReport = async () => {
    if (!selectedForecast) {
      setMessage('Please select a forecast');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await api.get(
        `/reports/forecast/${selectedForecast}?format=excel`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `forecast_report_${selectedForecast}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage('Excel report downloaded successfully!');
    } catch (error) {
      setMessage('Error downloading Excel report');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendEmail = async () => {
    if (!selectedForecast || !email) {
      setMessage('Please select a forecast and enter an email');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      await api.post('/reports/send-email', {
        forecast_id: selectedForecast,
        recipient: email,
        type: 'forecast'
      });

      setMessage(`Email sent successfully to ${email}!`);
      setEmail('');
    } catch (error) {
      setMessage('Error sending email');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Reports & Exports
      </Typography>

      {message && (
        <Alert
          severity={message.includes('Error') ? 'error' : 'success'}
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Select Forecast
            </Typography>

            <FormControl fullWidth>
              <InputLabel>Forecast</InputLabel>
              <Select
                value={selectedForecast}
                label="Forecast"
                onChange={(e) => setSelectedForecast(e.target.value)}
              >
                {forecasts.map((forecast) => (
                  <MenuItem key={forecast.forecast_id} value={forecast.forecast_id}>
                    Forecast #{forecast.forecast_id} - {forecast.forecast_date}
                    ({forecast.predicted_customers} customers, {Math.round(forecast.confidence_level * 100)}% confidence)
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <PictureAsPdf sx={{ mr: 1, color: 'error.main' }} />
              <Typography variant="h6">
                PDF Reports
              </Typography>
            </Box>

            <Typography variant="body2" color="text.secondary" paragraph>
              Download comprehensive PDF reports for forecasts and inventory.
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<Assessment />}
                onClick={handleDownloadForecastReport}
                disabled={loading || !selectedForecast}
                fullWidth
              >
                {loading ? <CircularProgress size={24} /> : 'Download Forecast Report'}
              </Button>

              <Button
                variant="contained"
                color="success"
                startIcon={<TableChart />}
                onClick={handleDownloadInventoryReport}
                disabled={loading || !selectedForecast}
                fullWidth
              >
                {loading ? <CircularProgress size={24} /> : 'Download Inventory Report'}
              </Button>

              <Button
                variant="outlined"
                color="success"
                startIcon={<TableChart />}
                onClick={handleDownloadExcelReport}
                disabled={loading || !selectedForecast}
                fullWidth
              >
                {loading ? <CircularProgress size={24} /> : 'Export to Excel'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Email sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">
                Email Reports
              </Typography>
            </Box>

            <Typography variant="body2" color="text.secondary" paragraph>
              Send forecast reports directly to your email.
            </Typography>

            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              sx={{ mb: 2 }}
              placeholder="manager@restaurant.com"
            />

            <Button
              variant="contained"
              startIcon={<Email />}
              onClick={handleSendEmail}
              disabled={loading || !selectedForecast || !email}
              fullWidth
            >
              {loading ? <CircularProgress size={24} /> : 'Send Email'}
            </Button>

            <Alert severity="info" sx={{ mt: 2 }}>
              Note: Email service requires SMTP configuration in backend
            </Alert>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Available Report Types
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Forecast Report</strong>
                </Typography>
                <ul>
                  <li>Next day and weekly predictions</li>
                  <li>Item-level demand forecast</li>
                  <li>Model confidence metrics</li>
                  <li>Visual charts and graphs</li>
                </ul>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Inventory Report</strong>
                </Typography>
                <ul>
                  <li>Shopping list with quantities</li>
                  <li>Estimated costs</li>
                  <li>Purchase orders by supplier</li>
                  <li>Ingredient breakdown</li>
                </ul>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ReportsPage;
