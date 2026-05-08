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
  TableRow
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
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

      // Preview file info
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
        headers: {
          'Content-Type': 'multipart/form-data'
        }
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
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Sales Data
      </Typography>

      <Paper sx={{ p: 4, mb: 3 }}>
        <Box
          sx={{
            border: '2px dashed #ccc',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            bgcolor: 'grey.50'
          }}
        >
          <CloudUpload sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />

          <Typography variant="h6" gutterBottom>
            Upload CSV or Excel File
          </Typography>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Supported formats: .csv, .xlsx, .xls
          </Typography>

          <input
            accept=".csv,.xlsx,.xls"
            style={{ display: 'none' }}
            id="file-upload"
            type="file"
            onChange={handleFileSelect}
          />

          <label htmlFor="file-upload">
            <Button variant="outlined" component="span">
              Choose File
            </Button>
          </label>

          <Box sx={{ mt: 3, maxWidth: 200, mx: 'auto' }}>
            <Typography variant="body2" gutterBottom>
              Target Outlet ID
            </Typography>
            <input
              type="number"
              value={outletId}
              onChange={(e) => setOutletId(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ccc'
              }}
            />
          </Box>
        </Box>

        {preview && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Selected File:
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Name:</strong></TableCell>
                    <TableCell>{preview.name}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Size:</strong></TableCell>
                    <TableCell>{preview.size}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Type:</strong></TableCell>
                    <TableCell>{preview.type}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Button
              variant="contained"
              fullWidth
              sx={{ mt: 3 }}
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? 'Uploading...' : 'Upload File'}
            </Button>
          </Box>
        )}

        {uploading && <LinearProgress sx={{ mt: 2 }} />}

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {uploadResult && (
          <Alert severity="success" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Upload Successful!</strong>
            </Typography>
            <Typography variant="body2">
              Records added: {uploadResult.records_added}
            </Typography>
          </Alert>
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Data Requirements
        </Typography>

        <Typography variant="body2">
          Your CSV/Excel file should contain the following columns:
        </Typography>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Column Name</strong></TableCell>
                <TableCell><strong>Required</strong></TableCell>
                <TableCell><strong>Description</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>date</TableCell>
                <TableCell>Yes</TableCell>
                <TableCell>Date of sale (YYYY-MM-DD)</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>customer_count</TableCell>
                <TableCell>Yes</TableCell>
                <TableCell>Number of customers</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>food_item</TableCell>
                <TableCell>No</TableCell>
                <TableCell>Name of food item sold</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>quantity_sold</TableCell>
                <TableCell>Yes</TableCell>
                <TableCell>Quantity sold</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>revenue</TableCell>
                <TableCell>No</TableCell>
                <TableCell>Revenue amount</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default DataUpload;