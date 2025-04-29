import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Typography,
  CircularProgress
} from '@mui/material';
import LanguageIcon from '@mui/icons-material/Language';

const LanguageSelector = () => {
  const [detectedLanguage, setDetectedLanguage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { i18n } = useTranslation();

  useEffect(() => {
    detectLanguage();
  }, []);

  const detectLanguage = async () => {
    try {
      setLoading(true);
      const response = await fetch('/detect-language');
      const data = await response.json();
      setDetectedLanguage(data);
      // Set the initial language in i18n
      i18n.changeLanguage(data.detected_language);
    } catch (err) {
      setError('Failed to detect language');
      console.error('Language detection error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageChange = async (event) => {
    const newLanguage = event.target.value;
    try {
      // Update the language in i18n
      await i18n.changeLanguage(newLanguage);
      // You might want to store the user's preference in localStorage
      localStorage.setItem('preferredLanguage', newLanguage);
    } catch (err) {
      console.error('Language change error:', err);
    }
  };

  if (loading) {
    return (
      <Box display="flex" alignItems="center" gap={1}>
        <CircularProgress size={20} />
        <Typography>Detecting language...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Typography color="error">
        {error}
      </Typography>
    );
  }

  return (
    <Box display="flex" alignItems="center" gap={2}>
      <LanguageIcon color="primary" />
      <FormControl size="small" sx={{ minWidth: 120 }}>
        <InputLabel id="language-select-label">Language</InputLabel>
        <Select
          labelId="language-select-label"
          id="language-select"
          value={i18n.language}
          label="Language"
          onChange={handleLanguageChange}
        >
          <MenuItem value="en">English</MenuItem>
          <MenuItem value="es">Español</MenuItem>
          <MenuItem value="fr">Français</MenuItem>
          <MenuItem value="de">Deutsch</MenuItem>
          <MenuItem value="it">Italiano</MenuItem>
          <MenuItem value="pt">Português</MenuItem>
          <MenuItem value="ru">Русский</MenuItem>
          <MenuItem value="zh">中文</MenuItem>
          <MenuItem value="ja">日本語</MenuItem>
          <MenuItem value="ko">한국어</MenuItem>
        </Select>
      </FormControl>
      {detectedLanguage && (
        <Typography variant="body2" color="textSecondary">
          Detected: {detectedLanguage.language_name}
        </Typography>
      )}
    </Box>
  );
};

export default LanguageSelector; 