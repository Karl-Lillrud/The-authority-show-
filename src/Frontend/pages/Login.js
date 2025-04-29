import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../contexts/TranslationContext';
import useLanguageDetection from '../hooks/useLanguageDetection';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip
} from '@mui/material';
import { Language as LanguageIcon } from '@mui/icons-material';

const Login = () => {
  const navigate = useNavigate();
  const { detectedLanguage, loading: detectingLanguage, error: languageError } = useLanguageDetection();
  const { i18n, translateText, changeLanguage, isRTL } = useTranslation();
  const [formData, setFormData] = React.useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [showLanguageSelector, setShowLanguageSelector] = React.useState(false);

  // Effect to handle language detection and switching
  useEffect(() => {
    const handleLanguageSwitch = async () => {
      if (detectedLanguage && !detectingLanguage) {
        try {
          // Change the app's language
          await i18n.changeLanguage(detectedLanguage);
          
          // Translate the login page content
          const translations = await translateText({
            "login_title": "Login",
            "email_label": "Email",
            "password_label": "Password",
            "login_button": "Log In",
            "forgot_password": "Forgot Password?",
            "create_account": "Create Account"
          });

          // Update the page content with translations
          if (translations) {
            console.log('Login page translations:', translations);
          }
        } catch (err) {
          console.error('Error switching language:', err);
        }
      }
    };

    handleLanguageSwitch();
  }, [detectedLanguage, detectingLanguage, i18n, translateText]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        // Store the user's preferred language
        localStorage.setItem('preferredLanguage', detectedLanguage || 'en');
        navigate('/dashboard');
      } else {
        setError(data.message || 'Login failed');
      }
    } catch (err) {
      setError('An error occurred during login');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleLanguageChange = (event) => {
    changeLanguage(event.target.value);
  };

  if (detectingLanguage) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="background.default"
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          width: '100%',
          maxWidth: 400,
          position: 'relative'
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom align="center">
          {i18n.t('login_title')}
        </Typography>

        {/* Language Selector */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
          <LanguageIcon color="action" />
          <FormControl fullWidth size="small">
            <Select
              value={i18n.language}
              onChange={handleLanguageChange}
              sx={{ bgcolor: 'background.paper' }}
            >
              <MenuItem value="en">English</MenuItem>
              <MenuItem value="ar">العربية</MenuItem>
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
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {languageError && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {languageError}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label={i18n.t('email_label')}
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            margin="normal"
            required
          />

          <TextField
            fullWidth
            label={i18n.t('password_label')}
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            margin="normal"
            required
          />

          <Button
            fullWidth
            type="submit"
            variant="contained"
            color="primary"
            size="large"
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : i18n.t('login_button')}
          </Button>

          <Box mt={2} display="flex" justifyContent="space-between">
            <Button color="primary">
              {i18n.t('forgot_password')}
            </Button>
            <Button color="primary">
              {i18n.t('create_account')}
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default Login; 