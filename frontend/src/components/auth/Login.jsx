import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Alert,
  Divider,
  Chip,
  Fade,
  Stack,
  alpha
} from '@mui/material';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import api from '../../api/axios';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/auth/login', { username, password });
      const { token, user } = response.data;
      login(user, token);
      navigate('/dashboard');
    } catch (err) {
      if (err.code === 'ERR_NETWORK' || err.code === 'ECONNREFUSED') {
        if (username === 'admin' && password === 'admin123') {
          login({ id: 0, username: 'admin', role: 'admin' }, 'dev-token');
          navigate('/dashboard');
        } else {
          setError('Backend offline. Use admin / admin123 for demo.');
        }
      } else {
        setError(err.response?.data?.error || 'Authentication failed.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'
    }}>
      <Fade in={true} timeout={1000}>
        <Paper sx={{
          display: 'flex',
          width: { xs: '90%', sm: '450px', md: '900px' },
          height: { md: '600px' },
          borderRadius: 6,
          overflow: 'hidden',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.15)'
        }}>
          {/* Left Side - Brand (Hidden on mobile) */}
          <Box sx={{
            display: { xs: 'none', md: 'flex' },
            flex: 1,
            background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            color: 'white',
            flexDirection: 'column',
            justifyContent: 'center',
            p: 6,
            position: 'relative'
          }}>
            <Stack spacing={2} sx={{ zIndex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{ p: 1, bgcolor: 'white', borderRadius: 2 }}>
                  <RestaurantIcon sx={{ color: '#6366f1' }} />
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 800, letterSpacing: '-1px' }}>ForeCastPro</Typography>
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>Precision Food Supply Management</Typography>
              <Typography variant="body1" sx={{ opacity: 0.8, lineHeight: 1.6 }}>
                Harnessing AI to predict demand, optimize inventory, and eliminate food waste across your network.
              </Typography>
            </Stack>

            <Box sx={{
              position: 'absolute',
              bottom: -50,
              right: -50,
              width: 300,
              height: 300,
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.1)',
              backdropFilter: 'blur(10px)'
            }} />
          </Box>

          {/* Right Side - Form */}
          <Box sx={{ flex: 1, p: { xs: 4, md: 8 }, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>Welcome Back</Typography>
              <Typography variant="body2" color="text.secondary">Enter your credentials to access the intelligence suite.</Typography>
            </Box>

            {error && <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }}>{error}</Alert>}

            <form onSubmit={handleSubmit}>
              <Stack spacing={3}>
                <TextField
                  label="Username"
                  fullWidth
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
                />
                <TextField
                  label="Password"
                  type="password"
                  fullWidth
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
                />
                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  disabled={loading}
                  sx={{
                    py: 1.5,
                    borderRadius: 3,
                    fontWeight: 700,
                    fontSize: '1rem',
                    boxShadow: '0 10px 15px -3px rgba(99, 102, 241, 0.3)'
                  }}
                >
                  {loading ? 'Authenticating...' : 'Sign In'}
                </Button>
              </Stack>

              <Divider sx={{ my: 4 }}>
                <Chip label="Demo Access" size="small" variant="outlined" />
              </Divider>

              <Box sx={{ p: 2.5, bgcolor: alpha('#6366f1', 0.05), borderRadius: 4, border: '1px dashed', borderColor: alpha('#6366f1', 0.2) }}>
                <Stack direction="row" spacing={2} sx={{ mb: 1, alignItems: 'center' }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: '#4f46e5' }}>ADMIN</Typography>
                  <Typography variant="caption" color="text.secondary">admin / admin123</Typography>
                </Stack>
                <Typography variant="caption" sx={{ fontStyle: 'italic', color: '#64748b' }}>
                  Use these credentials to explore the system features.
                </Typography>
              </Box>
            </form>
          </Box>
        </Paper>
      </Fade>
    </Box>
  );
};

export default Login;