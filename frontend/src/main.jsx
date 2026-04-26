/**
 * Application Entry Point
 * 
 * Initializes and renders the React application.
 *
 * Author: Carl Ikai
 * Project: Job Hunter AI Tool
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

/* Render React application into root DOM node */
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)