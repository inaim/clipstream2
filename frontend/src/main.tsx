import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { LanguageProvider } from './contexts/LanguageContext';
import App from './App.tsx';
import './index.css';
// Attach compatibility supabase to window for older modules that reference it
import { surreal } from './lib/surrealdb';
(window as any).surreal = surreal;
(window as any).supabase = surreal; // legacy alias for migration

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LanguageProvider>
      <App />
    </LanguageProvider>
  </StrictMode>
);
