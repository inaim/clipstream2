import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.tsx';
import './index.css';
// Attach compatibility supabase to window for older modules that reference it
import { surreal } from './lib/surrealdb';
(window as any).surreal = surreal;
(window as any).supabase = surreal; // legacy alias for migration

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
