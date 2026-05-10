import React from 'react';
import { Paper, Typography, Box, alpha } from '@mui/material';

const MetricCard = ({ title, value, icon: Icon, color = '#6366f1', trend }) => {
  return (
    <Paper
      sx={{
        p: 3,
        height: '100%',
        borderRadius: 4,
        position: 'relative',
        overflow: 'hidden',
        transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 24px -10px rgba(0,0,0,0.1)'
        }
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box
          sx={{
            p: 1.5,
            borderRadius: 3,
            backgroundColor: alpha(color, 0.1),
            color: color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <Icon fontSize="medium" />
        </Box>
        {trend && (
          <Typography
            variant="caption"
            sx={{
              fontWeight: 700,
              color: trend.includes('+') || trend.includes('Good') || trend.includes('High') || trend.includes('Stable') ? '#10b981' : '#f59e0b',
              backgroundColor: alpha(trend.includes('+') || trend.includes('Good') || trend.includes('High') || trend.includes('Stable') ? '#10b981' : '#f59e0b', 0.1),
              px: 1,
              py: 0.5,
              borderRadius: 1.5
            }}
          >
            {trend}
          </Typography>
        )}
      </Box>

      <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 600, mb: 0.5, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {title}
      </Typography>

      <Typography variant="h4" sx={{
        fontWeight: 800,
        color: '#1e293b',
        letterSpacing: '-1px',
        fontSize: { xs: '1.75rem', sm: '2.125rem' }
      }}>
        {value}
      </Typography>

      {/* Subtle background decoration */}
      <Box
        sx={{
          position: 'absolute',
          bottom: -20,
          right: -20,
          opacity: 0.03,
          transform: 'rotate(-15deg)'
        }}
      >
        <Icon sx={{ fontSize: 120 }} />
      </Box>
    </Paper>
  );
};

export default MetricCard;