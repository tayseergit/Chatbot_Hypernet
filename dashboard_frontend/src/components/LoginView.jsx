import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeOff, AlertTriangle } from 'lucide-react';

export default function LoginView() {
  const { login } = useAuth();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isCapsLock, setIsCapsLock] = useState(false);

  const handleKeyDown = (e) => {
    if (e.getModifierState && e.getModifierState('CapsLock')) {
      setIsCapsLock(true);
    } else {
      setIsCapsLock(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMsg('يرجى إدخال اسم المستخدم وكلمة المرور');
      return;
    }

    setIsLoading(true);
    setErrorMsg('');

    try {
      await login(username.trim(), password);
    } catch (err) {
      setErrorMsg(err.message || 'فشل تسجيل الدخول. يرجى التحقق من البيانات.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100%',
        backgroundColor: '#ffffff',
        display: 'flex',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: "'Inter', 'Cairo', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Top Right: Official Hypernet Brand Logo */}
      <div
        style={{
          position: 'absolute',
          top: '32px',
          right: '48px',
          zIndex: 20,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '2px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '28px',
              fontWeight: 900,
              letterSpacing: '2px',
              color: '#009b4d',
              fontFamily: "'Arial Black', 'Inter', sans-serif",
              lineHeight: 1,
            }}
          >
            HЧPER
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {/* Wifi Wave icon */}
            <svg width="24" height="18" viewBox="0 0 24 18" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M12 15C12.8284 15 13.5 14.3284 13.5 13.5C13.5 12.6716 12.8284 12 12 12C11.1716 12 10.5 12.6716 10.5 13.5C10.5 14.3284 11.1716 15 12 15Z"
                fill="#009b4d"
              />
              <path
                d="M7.05 9.05C9.78 6.32 14.22 6.32 16.95 9.05"
                stroke="#009b4d"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <path
                d="M3.5 5.5C8.2 0.8 15.8 0.8 20.5 5.5"
                stroke="#009b4d"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
            <span
              style={{
                fontSize: '28px',
                fontWeight: 900,
                letterSpacing: '2px',
                color: '#009b4d',
                fontFamily: "'Arial Black', 'Inter', sans-serif",
                lineHeight: 1,
                marginTop: '-2px',
              }}
            >
              ПET
            </span>
          </div>
        </div>
        <span
          style={{
            fontSize: '11px',
            fontWeight: 700,
            color: '#009b4d',
            letterSpacing: '0.5px',
            fontFamily: "'Cairo', sans-serif",
          }}
        >
          مزود خدمة الإنترنت
        </span>
      </div>

      {/* Main 2-Column Container */}
      <div
        style={{
          width: '100%',
          display: 'flex',
          flexDirection: 'row',
          minHeight: '100vh',
        }}
      >
        {/* Left Column: Sign In Form */}
        <div
          style={{
            flex: '0 0 45%',
            minWidth: '360px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '40px 48px',
            position: 'relative',
            zIndex: 10,
          }}
        >
          <div style={{ width: '100%', maxWidth: '340px' }}>
            {/* Title */}
            <h1
              style={{
                fontSize: '22px',
                fontWeight: 700,
                color: '#1e293b',
                textAlign: 'center',
                marginBottom: '32px',
                letterSpacing: '-0.3px',
              }}
            >
              Sign in to Hyper CRM
            </h1>

            {/* Error Notification */}
            {errorMsg && (
              <div
                style={{
                  background: '#fef2f2',
                  border: '1px solid #fecaca',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  marginBottom: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  color: '#dc2626',
                  fontSize: '12px',
                  fontWeight: 600,
                  animation: 'shake 0.3s ease',
                }}
              >
                <AlertTriangle size={16} style={{ flexShrink: 0 }} />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit}>
              {/* Username Input with top-right floating label */}
              <div style={{ marginBottom: '16px', position: 'relative' }}>
                <div
                  style={{
                    backgroundColor: '#eaf1fa',
                    borderRadius: '8px',
                    padding: '6px 14px 8px 14px',
                    border: '1px solid transparent',
                    transition: 'all 0.2s ease',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#93c5fd')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = 'transparent')}
                >
                  <label
                    style={{
                      display: 'block',
                      fontSize: '10px',
                      color: '#94a3b8',
                      fontWeight: 500,
                      textAlign: 'right',
                      marginBottom: '2px',
                      userSelect: 'none',
                    }}
                  >
                    Username
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={isLoading}
                    autoFocus
                    placeholder="Enter username"
                    style={{
                      width: '100%',
                      background: 'transparent',
                      border: 'none',
                      outline: 'none',
                      fontSize: '14px',
                      fontWeight: 500,
                      color: '#1e293b',
                      textAlign: 'center',
                      fontFamily: 'inherit',
                      padding: 0,
                    }}
                  />
                </div>
              </div>

              {/* Password Input with top-right floating label & left toggle icon */}
              <div style={{ marginBottom: '24px', position: 'relative' }}>
                <div
                  style={{
                    backgroundColor: '#eaf1fa',
                    borderRadius: '8px',
                    padding: '6px 14px 8px 14px',
                    border: '1px solid transparent',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    transition: 'all 0.2s ease',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#93c5fd')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = 'transparent')}
                >
                  <label
                    style={{
                      display: 'block',
                      fontSize: '10px',
                      color: '#94a3b8',
                      fontWeight: 500,
                      textAlign: 'right',
                      marginBottom: '2px',
                      userSelect: 'none',
                    }}
                  >
                    Password
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    {/* Left Eye Toggle Icon */}
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      tabIndex={-1}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: 0,
                        marginRight: '8px',
                        color: '#94a3b8',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'color 0.2s',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#475569')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>

                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyDown={handleKeyDown}
                      onKeyUp={handleKeyDown}
                      disabled={isLoading}
                      placeholder="••••••••••"
                      style={{
                        width: '100%',
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        fontSize: '14px',
                        fontWeight: 500,
                        color: '#1e293b',
                        textAlign: 'center',
                        letterSpacing: showPassword ? 'normal' : '2px',
                        fontFamily: 'inherit',
                        padding: 0,
                      }}
                    />
                  </div>
                </div>

                {/* Caps Lock Alert */}
                {isCapsLock && (
                  <div
                    style={{
                      color: '#d97706',
                      fontSize: '11px',
                      fontWeight: 600,
                      marginTop: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <AlertTriangle size={12} /> Caps Lock is ON
                  </div>
                )}
              </div>

              {/* Login Button */}
              <button
                type="submit"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '44px',
                  backgroundColor: '#1b2533',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 600,
                  fontFamily: 'inherit',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'background-color 0.2s, transform 0.1s',
                  boxShadow: '0 2px 8px rgba(27, 37, 51, 0.18)',
                  opacity: isLoading ? 0.8 : 1,
                }}
                onMouseEnter={(e) => {
                  if (!isLoading) e.currentTarget.style.backgroundColor = '#0f172a';
                }}
                onMouseLeave={(e) => {
                  if (!isLoading) e.currentTarget.style.backgroundColor = '#1b2533';
                }}
              >
                {isLoading ? (
                  <>
                    <span
                      style={{
                        width: '16px',
                        height: '16px',
                        border: '2px solid rgba(255, 255, 255, 0.3)',
                        borderTopColor: '#ffffff',
                        borderRadius: '50%',
                        display: 'inline-block',
                        animation: 'spin 0.8s linear infinite',
                      }}
                    />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <span>Login</span>
                )}
              </button>
            </form>
          </div>

          {/* Bottom Left: Assistant Floating Widget */}
          <div
            style={{
              position: 'fixed',
              bottom: '24px',
              left: '24px',
              width: '46px',
              height: '46px',
              borderRadius: '50%',
              backgroundColor: '#ffffff',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.12), 0 1px 3px rgba(0,0,0,0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s',
              zIndex: 30,
            }}
            title="Hypernet AI Support"
            onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.08)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
          >
            {/* 4 Colored Dots / Assistant Icon */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#4285F4' }} />
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#EA4335' }} />
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#FBBC05' }} />
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#34A853' }} />
            </div>
          </div>
        </div>

        {/* Right Column: 3D Illustration Area */}
        <div
          style={{
            flex: '1 1 55%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '40px',
            position: 'relative',
          }}
        >
          {/* Subtle Ambient Background Gradient */}
          <div
            style={{
              position: 'absolute',
              width: '450px',
              height: '450px',
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(234, 241, 250, 0.8) 0%, rgba(255, 255, 255, 0) 70%)',
              pointerEvents: 'none',
            }}
          />

          {/* 3D Dashboard Claymorphism Render */}
          <img
            src="/login_illustration.jpg"
            alt="Hypernet CRM Analytics Illustration"
            style={{
              maxWidth: '560px',
              width: '100%',
              height: 'auto',
              objectFit: 'contain',
              position: 'relative',
              zIndex: 2,
              filter: 'drop-shadow(0 20px 35px rgba(0, 0, 0, 0.06))',
              userSelect: 'none',
              pointerEvents: 'none',
            }}
          />
        </div>
      </div>
    </div>
  );
}
