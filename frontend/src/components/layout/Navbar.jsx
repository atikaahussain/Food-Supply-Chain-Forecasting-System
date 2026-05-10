import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Box,
  Tooltip
} from '@mui/material';
import {
  AccountCircle,
  Logout,
  Notifications
} from '@mui/icons-material';

const Navbar = () => {
  const [anchorEl, setAnchorEl] = React.useState(null);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(10px)',
        color: '#1e293b',
        boxShadow: 'none',
        borderBottom: '1px solid #f1f5f9',
      }}
    >
      <Toolbar sx={{ justifyContent: 'flex-end', minHeight: '70px !important' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Notifications">
            <IconButton size="medium" sx={{ color: '#64748b' }}>
              <Notifications />
            </IconButton>
          </Tooltip>

          <Box sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            ml: 2,
            pl: 2,
            borderLeft: '1px solid #e2e8f0'
          }}>
            <Box sx={{ textAlign: 'right', display: { xs: 'none', sm: 'block' } }}>
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#1e293b', lineHeight: 1.2 }}>
                {user?.username || 'Admin User'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 500 }}>
                {user?.role || 'Administrator'}
              </Typography>
            </Box>

            <IconButton
              onClick={handleMenu}
              sx={{ p: 0.5, border: '2px solid #e2e8f0' }}
            >
              <Avatar
                sx={{
                  width: 35,
                  height: 35,
                  bgcolor: '#6366f1',
                  fontSize: '0.9rem',
                  fontWeight: 600
                }}
              >
                {user?.username?.charAt(0).toUpperCase() || 'A'}
              </Avatar>
            </IconButton>
          </Box>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleClose}
            PaperProps={{
              sx: {
                mt: 1.5,
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                borderRadius: '12px',
                minWidth: 180,
                border: '1px solid #f1f5f9'
              }
            }}
          >
            <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid #f1f5f9' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                Account Settings
              </Typography>
            </Box>
            <MenuItem onClick={handleLogout} sx={{ py: 1.5, color: '#ef4444' }}>
              <Logout fontSize="small" sx={{ mr: 1.5 }} />
              <Typography variant="body2" sx={{ fontWeight: 600 }}>Logout</Typography>
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;