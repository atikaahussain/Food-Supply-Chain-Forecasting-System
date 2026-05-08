import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  Button,
  IconButton,
  Divider,
  Alert as MuiAlert
} from '@mui/material';
import {
  Warning,
  CheckCircle,
  Error,
  Info,
  Close
} from '@mui/icons-material';
import api from '../../api/axios';

const AlertsPanel = ({ outletId }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [outletId]);

  const fetchAlerts = async () => {
    try {
      const response = await api.get(`/inventory/alerts/${outletId}`);
      setAlerts(response.data.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await api.post(`/inventory/alerts/resolve/${alertId}`);
      fetchAlerts();
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const handleGenerateAlerts = async () => {
    setLoading(true);
    try {
      const forecastRes = await api.get('/forecast/latest/1');
      const forecastId = forecastRes.data.forecast_id;
      
      await api.post(`/inventory/alerts/generate/${outletId}`, {
        forecast_id: forecastId
      });
      
      fetchAlerts();
    } catch (error) {
      console.error('Error generating alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high':
        return <Error />;
      case 'medium':
        return <Warning />;
      case 'low':
        return <Info />;
      default:
        return <Info />;
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">
          Active Alerts ({alerts.length})
        </Typography>
        <Button
          variant="outlined"
          size="small"
          onClick={handleGenerateAlerts}
          disabled={loading}
        >
          {loading ? 'Checking...' : 'Check Now'}
        </Button>
      </Box>

      {alerts.length === 0 ? (
        <MuiAlert severity="success" icon={<CheckCircle />}>
          No active alerts. Everything looks good! ✨
        </MuiAlert>
      ) : (
        <List>
          {alerts.map((alert, index) => (
            <React.Fragment key={alert.id}>
              <ListItem
                alignItems="flex-start"
                secondaryAction={
                  <IconButton
                    edge="end"
                    onClick={() => handleResolve(alert.id)}
                    size="small"
                  >
                    <Close />
                  </IconButton>
                }
              >
                <Box sx={{ mr: 2, mt: 1 }}>
                  {getSeverityIcon(alert.severity)}
                </Box>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle2">
                        {alert.type?.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Chip
                        label={alert.severity}
                        size="small"
                        color={getSeverityColor(alert.severity)}
                      />
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body2" color="text.primary">
                        {alert.message}
                      </Typography>
                      {alert.ingredient && (
                        <Typography variant="caption" color="text.secondary">
                          Ingredient: {alert.ingredient}
                        </Typography>
                      )}
                      <Typography variant="caption" display="block" color="text.secondary">
                        {new Date(alert.created_at).toLocaleString()}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
              {index < alerts.length - 1 && <Divider component="li" />}
            </React.Fragment>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default AlertsPanel;
