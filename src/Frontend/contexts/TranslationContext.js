import React, { createContext, useContext, useState, useEffect } from 'react';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Define RTL languages
const RTL_LANGUAGES = ['ar', 'he', 'fa'];

// Initialize i18next
i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation: {
          // English translations
        }
      },
      ar: {
        translation: {
          login_title: "تسجيل الدخول",
          email_label: "البريد الإلكتروني",
          password_label: "كلمة المرور",
          login_button: "تسجيل الدخول",
          forgot_password: "نسيت كلمة المرور؟",
          create_account: "إنشاء حساب",
          welcome_message: "مرحباً بك في تطبيقنا",
          loading: "جاري التحميل..."
        }
      },
      // Add other languages here
    },
    lng: 'en', // default language
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

const TranslationContext = createContext();

export const TranslationProvider = ({ children }) => {
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [isLoading, setIsLoading] = useState(true);
  const [isRTL, setIsRTL] = useState(false);

  useEffect(() => {
    initializeLanguage();
  }, []);

  const initializeLanguage = async () => {
    try {
      // First check for saved language preference
      const savedLanguage = localStorage.getItem('preferredLanguage');
      if (savedLanguage) {
        setCurrentLanguage(savedLanguage);
        i18n.changeLanguage(savedLanguage);
        setIsRTL(RTL_LANGUAGES.includes(savedLanguage));
        setIsLoading(false);
        return;
      }

      // If no saved preference, detect browser language
      const response = await fetch('/detect-language');
      const data = await response.json();
      
      if (data.detected_language) {
        setCurrentLanguage(data.detected_language);
        i18n.changeLanguage(data.detected_language);
        setIsRTL(RTL_LANGUAGES.includes(data.detected_language));
      }
    } catch (error) {
      console.error('Failed to initialize language:', error);
      // Fallback to English
      setCurrentLanguage('en');
      i18n.changeLanguage('en');
      setIsRTL(false);
    } finally {
      setIsLoading(false);
    }
  };

  const changeLanguage = async (language) => {
    try {
      await i18n.changeLanguage(language);
      setCurrentLanguage(language);
      setIsRTL(RTL_LANGUAGES.includes(language));
      localStorage.setItem('preferredLanguage', language);
    } catch (error) {
      console.error('Failed to change language:', error);
    }
  };

  const translateText = async (text) => {
    try {
      const response = await fetch('/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          target_language: currentLanguage
        })
      });
      const data = await response.json();
      return data.translated_text;
    } catch (error) {
      console.error('Translation failed:', error);
      return text; // Return original text if translation fails
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <TranslationContext.Provider
      value={{
        currentLanguage,
        changeLanguage,
        translateText,
        i18n,
        isRTL
      }}
    >
      <div dir={isRTL ? 'rtl' : 'ltr'}>
        {children}
      </div>
    </TranslationContext.Provider>
  );
};

export const useTranslation = () => {
  const context = useContext(TranslationContext);
  if (!context) {
    throw new Error('useTranslation must be used within a TranslationProvider');
  }
  return context;
};

export default TranslationContext; 