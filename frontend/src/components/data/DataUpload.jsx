import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stack,
  TextField,
  IconButton,
  Fade,
  alpha,
  Grid,
  Avatar
} from '@mui/material';
import { CloudUpload, Delete, InsertDriveFile, SyncAlt, Info } from '@mui/icons-material';
import api from '../../api/axios';

const DataUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState(null);
  const [outletId, setOutletId] = useState(1);

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
      setUploadResult(null);
      setPreview({
        name: selectedFile.name,
        size: (selectedFile.size / 1024).toFixed(2) + ' KB',
        type: selectedFile.type
      });
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('outlet_id', outletId);

    try {
      const response = await api.post('/data/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadResult(response.data);
      setFile(null);
      setPreview(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Fade in={true} timeout={800}>
      <Box sx={{ pb: 6 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: '-1px', mb: 0.5 }}>
            Data Import Center
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Feed your system with historical sales data to improve forecast accuracy.
          </Typography>
        </Box>

        <Grid container spacing={4}>
          <Grid item xs={12} lg={7}>
            <Paper sx={{ p: 4, borderRadius: 4 }}>
              <Box
                sx={{
                  border: '2px dashed #e2e8f0',
                  borderRadius: 4,
                  p: 6,
                  textAlign: 'center',
                  transition: 'all 0.2s ease',
                  bgcolor: 'rgba(99, 102, 241, 0.02)',
                  '&:hover': {
                    borderColor: '#6366f1',
                    bgcolor: 'rgba(99, 102, 241, 0.05)',
                  }
                }}
              >
                <CloudUpload sx={{ fontSize: 60, color: '#6366f1', mb: 2, opacity: 0.8 }} />
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                  Select Sales Dataset
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                  Drag and drop your .csv or .xlsx file here, or click to browse.
                </Typography>

                <input
                  accept=".csv,.xlsx,.xls"
                  style={{ display: 'none' }}
                  id="file-upload"
                  type="file"
                  onChange={handleFileSelect}
                />
                <label htmlFor="file-upload">
                  <Button variant="contained" component="span" sx={{ px: 4 }}>
                    Choose File
                  </Button>
                </label>
              </Box>

              {preview && (
                <Fade in={true}>
                  <Box sx={{ mt: 4, p: 3, borderRadius: 3, border: '1px solid #f1f5f9', bgcolor: '#f8fafc' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: '#6366f1' }}><InsertDriveFile /></Avatar>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{preview.name}</Typography>
                        <Typography variant="caption" color="text.secondary">{preview.size} • {preview.type || 'Binary'}</Typography>
                      </Box>
                      <IconButton onClick={() => { setFile(null); setPreview(null); }} color="error">
                        <Delete />
                      </IconButton>
                    </Box>

                    <Stack direction="row" spacing={2} sx={{ mt: 3, alignItems: 'center' }}>
                      <TextField
                        label="Location / Outlet ID"
                        type="number"
                        size="small"
                        value={outletId}
                        onChange={(e) => setOutletId(e.target.value)}
                        sx={{ maxWidth: 150 }}
                      />
                      <Button
                        variant="contained"
                        fullWidth
                        onClick={handleUpload}
                        disabled={uploading}
                        sx={{ py: 1 }}
                      >
                        {uploading ? 'Processing Data...' : 'Begin Upload'}
                      </Button>
                    </Stack>
                    {uploading && <LinearProgress sx={{ mt: 2, borderRadius: 2 }} />}
                  </Box>
                </Fade>
              )}

              {error && <Alert severity="error" sx={{ mt: 3, borderRadius: 3 }}>{error}</Alert>}
              {uploadResult && (
                <Alert severity="success" sx={{ mt: 3, borderRadius: 3 }}>
                  <Typography variant="subtitle2">Success: {uploadResult.message || 'Data integrated successfully'}</Typography>
                  {uploadResult.records_added > 0 && <Typography variant="caption">Imported {uploadResult.records_added} new sales records.</Typography>}
                </Alert>
              )}
            </Paper>

            <Paper sx={{ p: 4, mt: 4, borderRadius: 4, border: '1px solid #e2e8f0', background: 'linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <SyncAlt sx={{ color: '#ec4899' }} />
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>Data Synchronization</Typography>
                  <Typography variant="body2" color="text.secondary">Maintain consistency across your item names and categories.</Typography>
                </Box>
              </Box>
              <Button
                variant="outlined"
                color="secondary"
                onClick={async () => {
                  setUploading(true);
                  try {
                    const res = await api.post('/data/fix-names');
                    setUploadResult({ message: res.data.message });
                  } catch (err) {
                    setError('Sync failed');
                  } finally {
                    setUploading(false);
                  }
                }}
                disabled={uploading}
                startIcon={<SyncAlt />}
                sx={{ mt: 1 }}
              >
                Synchronize Item Mapping
              </Button>
            </Paper>
          </Grid>

          <Grid item xs={12} lg={5}>
            <Paper sx={{ p: 4, borderRadius: 4, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <Info sx={{ color: '#6366f1' }} />
                <Typography variant="h6" sx={{ fontWeight: 700 }}>Data Blueprint</Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                Ensure your file adheres to the following structure for optimal model training.
              </Typography>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700, color: '#64748b' }}>Attribute</TableCell>
                      <TableCell sx={{ fontWeight: 700, color: '#64748b' }}>Type</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {[
                      { name: 'date', desc: 'Transaction Date (YYYY-MM-DD)' },
                      { name: 'customer_count', desc: 'Footfall total' },
                      { name: 'meal_id / food_item', desc: 'Identification' },
                      { name: 'num_orders / quantity', desc: 'Units sold' },
                      { name: 'checkout_price / revenue', desc: 'Financial value' }
                    ].map((col) => (
                      <TableRow key={col.name}>
                        <TableCell sx={{ fontWeight: 600 }}>{col.name}</TableCell>
                        <TableCell color="text.secondary"><Typography variant="caption">{col.desc}</Typography></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Box sx={{ mt: 4, p: 3, borderRadius: 3, bgcolor: alpha('#6366f1', 0.05), border: '1px solid', borderColor: alpha('#6366f1', 0.2) }}>
                <Typography variant="subtitle2" sx={{ color: '#4f46e5', fontWeight: 700, mb: 1 }}>Pro Tip</Typography>
                <Typography variant="body2" color="text.secondary">
                  The more historical data you provide, the better our AI can understand seasonal patterns and holidays!
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
};

export default DataUpload;