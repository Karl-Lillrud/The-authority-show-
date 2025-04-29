import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { TranslationProvider } from './contexts/TranslationContext';
import Navigation from './components/Navigation';
import TranslationManagerRoute from './routes/TranslationManagerRoute';
import LanguageSelector from './components/LanguageSelector';
import Login from './pages/Login';
// ... other imports

const App = () => {
  return (
    <TranslationProvider>
      <Router>
        <div className="app">
          <Navigation />
          <main>
            <Routes>
              <Route path="/translation-manager" element={<TranslationManagerRoute />} />
              <Route path="/login" element={<Login />} />
              {/* ... other routes */}
            </Routes>
          </main>
          <header>
            <LanguageSelector />
            {/* Other header components */}
          </header>
        </div>
      </Router>
    </TranslationProvider>
  );
};

export default App; 