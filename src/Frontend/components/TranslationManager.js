import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Language as LanguageIcon
} from '@mui/icons-material';

const TranslationManager = () => {
  const [languages, setLanguages] = useState({});
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [translations, setTranslations] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingKey, setEditingKey] = useState(null);
  const [editedValue, setEditedValue] = useState('');

  useEffect(() => {
    fetchLanguages();
  }, []);

  const fetchLanguages = async () => {
    try {
      setLoading(true);
      const response = await fetch('/languages');
      const data = await response.json();
      setLanguages(data.languages);
      if (Object.keys(data.languages).length > 0) {
        setSelectedLanguage(Object.keys(data.languages)[0]);
      }
    } catch (err) {
      setError('Failed to fetch languages');
      console.error('Error fetching languages:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTranslations = async (language) => {
    try {
      setLoading(true);
      const response = await fetch('/collect-and-translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_language: language
        })
      });
      const data = await response.json();
      if (data.translated_content) {
        setTranslations(data.translated_content);
      } else {
        setError('Failed to fetch translations');
      }
    } catch (err) {
      setError('Failed to fetch translations');
      console.error('Error fetching translations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedLanguage) {
      fetchTranslations(selectedLanguage);
    }
  }, [selectedLanguage]);

  const handleLanguageChange = (event) => {
    setSelectedLanguage(event.target.value);
  };

  const handleEdit = (key, value) => {
    setEditingKey(key);
    setEditedValue(value);
  };

  const handleSave = async (key) => {
    try {
      const updatedTranslations = {
        ...translations,
        [key]: editedValue
      };

      const response = await fetch('/translate-app', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: updatedTranslations,
          target_language: selectedLanguage
        })
      });

      const data = await response.json();
      if (data.translated_content) {
        setTranslations(data.translated_content);
        setSuccess('Translation saved successfully');
      } else {
        setError('Failed to save translation');
      }
    } catch (err) {
      setError('Failed to save translation');
      console.error('Error saving translation:', err);
    } finally {
      setEditingKey(null);
    }
  };

  const handleClearCache = async () => {
    try {
      const response = await fetch('/clear-cache', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          language: selectedLanguage
        })
      });
      if (response.ok) {
        setSuccess('Cache cleared successfully');
        fetchTranslations(selectedLanguage);
      } else {
        setError('Failed to clear cache');
      }
    } catch (err) {
      setError('Failed to clear cache');
      console.error('Error clearing cache:', err);
    }
  };

  const handleRefresh = () => {
    fetchTranslations(selectedLanguage);
  };

  if (loading && !translations) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Translation Manager
        </Typography>
        <Box display="flex" gap={2}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel id="language-select-label">Language</InputLabel>
            <Select
              labelId="language-select-label"
              value={selectedLanguage}
              label="Language"
              onChange={handleLanguageChange}
            >
              {Object.entries(languages).map(([code, name]) => (
                <MenuItem key={code} value={code}>
                  {name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Tooltip title="Refresh Translations">
            <IconButton onClick={handleRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear Cache">
            <IconButton onClick={handleClearCache}>
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Snackbar
          open={!!success}
          autoHideDuration={6000}
          onClose={() => setSuccess(null)}
        >
          <Alert severity="success" onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        </Snackbar>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Key</TableCell>
              <TableCell>Translation</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(translations).map(([key, value]) => (
              <TableRow key={key}>
                <TableCell>{key}</TableCell>
                <TableCell>
                  {editingKey === key ? (
                    <TextField
                      fullWidth
                      value={editedValue}
                      onChange={(e) => setEditedValue(e.target.value)}
                      onBlur={() => handleSave(key)}
                      autoFocus
                    />
                  ) : (
                    value
                  )}
                </TableCell>
                <TableCell>
                  <Tooltip title="Edit Translation">
                    <IconButton
                      size="small"
                      onClick={() => handleEdit(key, value)}
                    >
                      <SaveIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default TranslationManager; 