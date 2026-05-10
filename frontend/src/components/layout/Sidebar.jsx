import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Box,
  ListItemButton
} from '@mui/material';
import {
  Dashboard,
  UploadFile,
  Timeline,
  Inventory,
  Assessment,
  Restaurant
} from '@mui/icons-material';

const DRAWER_WIDTH = 260;

const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
  { text: 'Upload Data', icon: <UploadFile />, path: '/upload' },
  { text: 'Forecasts', icon: <Timeline />, path: '/forecast' },
  { text: 'Inventory', icon: <Inventory />, path: '/inventory' },
  { text: 'Reports', icon: <Assessment />, path: '/reports' }
];

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          backgroundColor: '#0f172a', // Dark slate
          color: '#94a3b8',
          borderRight: 'none',
        },
      }}
    >
      <Toolbar sx={{ px: 3, py: 4, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Box sx={{
          p: 1,
          borderRadius: '10px',
          backgroundColor: '#6366f1',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Restaurant sx={{ color: 'white' }} />
        </Box>
        <Typography variant="h6" sx={{
          fontWeight: 700,
          color: 'white',
          letterSpacing: '-0.5px'
        }}>
          ForeCastPro
        </Typography>
      </Toolbar>

      <List sx={{ px: 2, pt: 2 }}>
        {menuItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                selected={active}
                sx={{
                  borderRadius: '12px',
                  py: 1.5,
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(99, 102, 241, 0.15)',
                    color: '#818cf8',
                    '&:hover': {
                      backgroundColor: 'rgba(99, 102, 241, 0.25)',
                    },
                    '& .MuiListItemIcon-root': {
                      color: '#818cf8',
                    }
                  },
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    color: 'white',
                    '& .MuiListItemIcon-root': {
                      color: 'white',
                    }
                  }
                }}
              >
                <ListItemIcon sx={{
                  minWidth: 45,
                  color: active ? '#818cf8' : '#64748b',
                  transition: 'color 0.2s'
                }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '0.95rem',
                    fontWeight: active ? 600 : 500,
                    letterSpacing: '0.2px'
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ mt: 'auto', p: 3, mb: 2 }}>
        <Box sx={{
          p: 2.5,
          borderRadius: '16px',
          backgroundColor: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.2)'
        }}>
          <Typography variant="caption" sx={{ color: '#818cf8', fontWeight: 600, display: 'block', mb: 1 }}>
            SYSTEM STATUS
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981' }} />
            <Typography variant="body2" sx={{ color: '#cbd5e1', fontWeight: 500 }}>
              Live & Healthy
            </Typography>
          </Box>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Sidebar;