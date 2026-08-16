import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

const TOKEN_KEY = 'hypernet_admin_jwt';
const ADMIN_KEY = 'hypernet_admin_user';
const EXPIRES_KEY = 'hypernet_admin_expires_at';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || null);
  const [admin, setAdmin] = useState(() => {
    try {
      const saved = localStorage.getItem(ADMIN_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Force re-login if the stored admin object is from an older version (missing permissions)
        if (!parsed.permissions) {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(ADMIN_KEY);
          localStorage.removeItem(EXPIRES_KEY);
          return null;
        }
        return parsed;
      }
      return null;
    } catch {
      return null;
    }
  });
  const [expiresAt, setExpiresAt] = useState(() => localStorage.getItem(EXPIRES_KEY) || null);
  const [remainingSeconds, setRemainingSeconds] = useState(3600);
  const [isLoading, setIsLoading] = useState(true);

  // Global Logout
  const logout = useCallback(async (notifyServer = true) => {
    const currentToken = token || localStorage.getItem(TOKEN_KEY);
    if (notifyServer && currentToken) {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${currentToken}`
          }
        });
      } catch (err) {
        console.warn('Logout API error:', err);
      }
    }
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ADMIN_KEY);
    localStorage.removeItem(EXPIRES_KEY);
    setToken(null);
    setAdmin(null);
    setExpiresAt(null);
    setRemainingSeconds(0);
  }, [token]);

  // Global Login
  const login = async (username, password) => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      let data = {};
      try {
        data = await res.json();
      } catch {
        if (!res.ok) {
          throw new Error(
            res.status === 404
              ? 'تعذر الوصول للـ API (404). يرجى التأكد من تشغيل سيرفر الباك إند (Port 8000).'
              : `خطأ في استجابة الخادم (${res.status})`
          );
        }
      }

      if (!res.ok) {
        throw new Error(data.detail || 'فشل تسجيل الدخول. يرجى التحقق من اسم المستخدم وكلمة المرور.');
      }

      const accessToken = data.access_token;
      const adminUser = data.admin;
      const expiresInSec = data.expires_in || 3600;
      // Calculate absolute expiry epoch in milliseconds
      const expEpochMs = Date.now() + expiresInSec * 1000;

      localStorage.setItem(TOKEN_KEY, accessToken);
      localStorage.setItem(ADMIN_KEY, JSON.stringify(adminUser));
      localStorage.setItem(EXPIRES_KEY, String(expEpochMs));

      setToken(accessToken);
      setAdmin(adminUser);
      setExpiresAt(String(expEpochMs));
      setRemainingSeconds(expiresInSec);

      return adminUser;
    } catch (err) {
      if (err.name === 'TypeError' && err.message && err.message.toLowerCase().includes('fetch')) {
        throw new Error('تعذر الاتصال بسيرفر الباك إند (Port 8000). يرجى التأكد من تشغيله.');
      }
      throw err;
    }
  };

  // Setup Global Fetch Interceptor to attach Bearer Token automatically to all /api/ calls
  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async function (url, options = {}) {
      const isApi = typeof url === 'string' && url.includes('/api/');
      const isAuthLogin = typeof url === 'string' && url.includes('/api/auth/login');
      const storedToken = localStorage.getItem(TOKEN_KEY);

      if (isApi && !isAuthLogin && storedToken) {
        options.headers = {
          ...options.headers,
          'Authorization': `Bearer ${storedToken}`
        };
      }

      const response = await originalFetch(url, options);

      // Intercept 401 Unauthorized -> session expired
      if (response.status === 401 && isApi && !isAuthLogin) {
        console.warn('[AUTH] 401 Unauthorized encountered. Logging out...');
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(ADMIN_KEY);
        localStorage.removeItem(EXPIRES_KEY);
        setToken(null);
        setAdmin(null);
        setExpiresAt(null);
      }

      return response;
    };

    setIsLoading(false);

    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  // Timer countdown for active 60-minute session based on Epoch timestamp
  useEffect(() => {
    if (!expiresAt || !token) {
      setRemainingSeconds(0);
      return;
    }

    const expTime = parseInt(expiresAt, 10);
    if (!expTime || isNaN(expTime)) {
      return;
    }

    const updateTimer = () => {
      const now = Date.now();
      const diffSec = Math.max(0, Math.floor((expTime - now) / 1000));
      setRemainingSeconds(diffSec);

      if (diffSec <= 0) {
        console.warn('[AUTH] Session timed out (1 hour passed).');
        logout(false);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [expiresAt, token, logout]);

  // Formatted countdown string (e.g. "58:30")
  const formatRemainingTime = () => {
    const mins = Math.floor(remainingSeconds / 60);
    const secs = remainingSeconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const hasPermission = useCallback((permId) => {
    return admin?.permissions?.includes(permId) || false;
  }, [admin]);

  const value = {
    token,
    admin,
    isAuthenticated: !!token && !!admin,
    isLoading,
    login,
    logout,
    hasPermission,
    remainingSeconds,
    remainingFormatted: formatRemainingTime(),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
