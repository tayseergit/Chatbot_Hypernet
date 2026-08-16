import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

const originalFetch = window.fetch;
window.fetch = async (...args) => {
  let [resource, config] = args;
  
  if (typeof resource === 'string' && resource.includes('/api/')) {
    if (!resource.includes('/api/auth/login') && !resource.endsWith('/api/chat') && !resource.includes('/api/auth/logout')) {
      const token = localStorage.getItem('hypernet_admin_jwt');
      if (token) {
        config = config || {};
        config.headers = {
          ...config.headers,
          'Authorization': `Bearer ${token}`
        };
      }
    }
  }
  return originalFetch(resource, config);
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
