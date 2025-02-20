import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  Pagination,
  Stack,
  Snackbar,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { API_ENDPOINTS } from '../config/api';

interface ClassificationResult {
  id: number;
  content_type: string;
  content_hash: string;
  classification: string;
  confidence: number;
  metadata: {
    explanation: string;
    category_group_name: string;
  };
  created_at: string;
  rule: any;
  user: number;
  llm_provider: string;
  llm_model: string;
}

interface TextInputData {
  id: number;
  content: string;
  title: string;
  processed: boolean;
  classification_results: ClassificationResult[];
  created_at: string;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: TextInputData[];
}

export default function TextInput() {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [processedTexts, setProcessedTexts] = useState<TextInputData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(10);
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error'
  });
  const [providers, setProviders] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');

  const fetchProcessedTexts = useCallback(async (pageNumber: number) => {
    try {
      const response = await fetch(
        `${API_ENDPOINTS.TEXTS}?page=${pageNumber}&page_size=${pageSize}`,
        {
          headers: {
            'Authorization': `Token ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.ok) {
        const data: PaginatedResponse = await response.json();
        setProcessedTexts(data.results);
        setTotalPages(Math.ceil(data.count / pageSize));
      } else {
        throw new Error('Failed to fetch processed texts');
      }
    } catch (err) {
      setError('Error fetching processed texts');
    }
  }, [pageSize]);

  useEffect(() => {
    fetchProcessedTexts(page);
  }, [page, fetchProcessedTexts]);

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.LLM_PROVIDERS, {
          headers: {
            'Authorization': `Token ${localStorage.getItem('token')}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          setProviders(data.providers);
          // Set deepseek as default provider
          const defaultProvider = data.providers.find((p: string) => p === 'deepseek') || data.providers[0];
          setSelectedProvider(defaultProvider);
        } else {
          console.error('Failed to fetch providers:', response.status);
        }
      } catch (error) {
        console.error('Error fetching providers:', error);
      }
    };

    fetchProviders();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(API_ENDPOINTS.TEXTS, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          content, 
          title,
          llm_provider: selectedProvider 
        })
      });

      if (response.ok) {
        const result = await response.json();
        setContent('');
        setTitle('');
        
        // Refresh the first page after submission
        setPage(1);
        await fetchProcessedTexts(1);
        
        // Show success message if classification is available
        if (result.classification_results && result.classification_results.length > 0) {
          setNotification({
            open: true,
            message: `Text classified as: ${result.classification_results[0].classification} (${(result.classification_results[0].confidence * 100).toFixed(1)}% confidence)`,
            severity: 'success'
          });
        }
      } else {
        throw new Error('Failed to submit text');
      }
    } catch (err) {
      setError('Error submitting text');
      setNotification({
        open: true,
        message: 'Error submitting text',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
        <Typography variant="h4">
          Text Input
        </Typography>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel id="llm-provider-label">LLM Provider</InputLabel>
          <Select
            labelId="llm-provider-label"
            value={selectedProvider}
            label="LLM Provider"
            onChange={(e) => setSelectedProvider(e.target.value)}
          >
            {providers.map((provider) => (
              <MenuItem key={provider} value={provider}>
                {provider.charAt(0).toUpperCase() + provider.slice(1)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            margin="normal"
            required
            multiline
            rows={4}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Submit'}
          </Button>
        </form>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Typography variant="h5" gutterBottom>
        Processed Texts
      </Typography>

      <Grid container spacing={3}>
        {processedTexts.map((text) => (
          <Grid item xs={12} key={text.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {text.title}
                </Typography>
                <Typography color="text.secondary" paragraph>
                  {text.content}
                </Typography>
                {text.classification_results && text.classification_results.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    {text.classification_results.map((result, index) => (
                      <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                        <Typography variant="subtitle1" color="primary" gutterBottom>
                          Category Group: {result.metadata.category_group_name}
                        </Typography>
                        <Typography variant="subtitle2">
                          Classification: {result.classification}
                        </Typography>
                        <Typography variant="subtitle2">
                          Confidence: {(result.confidence * 100).toFixed(2)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          {result.metadata.explanation}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                )}
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Submitted on: {new Date(text.created_at).toLocaleString()} | 
                  Provider: {text.classification_results[0]?.llm_provider || 'unknown'} | 
                  Model: {text.classification_results[0]?.llm_model || 'unknown'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Stack spacing={2} alignItems="center" sx={{ mt: 3 }}>
        <Pagination
          count={totalPages}
          page={page}
          onChange={handlePageChange}
          color="primary"
        />
      </Stack>

      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
} 