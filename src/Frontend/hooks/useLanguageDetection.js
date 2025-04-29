import { useState, useEffect } from 'react';

const useLanguageDetection = () => {
  const [detectedLanguage, setDetectedLanguage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    detectLanguage();
  }, []);

  const detectLanguage = async () => {
    try {
      setLoading(true);
      const response = await fetch('/detect-language');
      const data = await response.json();
      setDetectedLanguage(data.detected_language);
    } catch (err) {
      setError('Failed to detect language');
      console.error('Language detection error:', err);
    } finally {
      setLoading(false);
    }
  };

  return { detectedLanguage, loading, error };
};

export default useLanguageDetection; 