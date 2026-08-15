import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeOff, AlertTriangle } from 'lucide-react';

/* ───────────────────────────────── Keyframes injected once ─────────────────────────────────── */
const STYLE = `
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');

@keyframes spin   { to { transform: rotate(360deg); } }
@keyframes shake  {
  0%,100% { transform: translateX(0); }
  20%,60% { transform: translateX(-6px); }
  40%,80% { transform: translateX(6px); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
* { box-sizing: border-box; }
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
  -webkit-box-shadow: 0 0 0 1000px #edf2f9 inset !important;
  -webkit-text-fill-color: #1e293b !important;
}
`;

/* ──────────────────────────── Hypernet Logo (faithful SVG recreation) ──────────────────────── */
function HypernetLogo({ size = 'md' }) {
  const scale = size === 'sm' ? 0.8 : 1;
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 0,
        transform: `scale(${scale})`,
        transformOrigin: 'top center',
        userSelect: 'none',
      }}
    >
      <span
        style={{
          fontFamily: "'Arial Black', 'Impact', sans-serif",
          fontSize: '19px',
          fontWeight: 900,
          letterSpacing: '3px',
          color: 'var(--primary)',
          lineHeight: 1,
          textTransform: 'uppercase',
        }}
      >
        HYPER
      </span>

      <svg
        width="36"
        height="22"
        viewBox="0 0 36 22"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ margin: '1px 0' }}
      >
        <circle cx="18" cy="19" r="2.5" fill="var(--primary)" />
        <path
          d="M11.5 13.5 C13.2 11 15.5 9.8 18 9.8 C20.5 9.8 22.8 11 24.5 13.5"
          stroke="var(--primary)"
          strokeWidth="2.8"
          strokeLinecap="round"
          fill="none"
        />
        <path
          d="M5.5 8 C9.5 3.5 13.5 1.5 18 1.5 C22.5 1.5 26.5 3.5 30.5 8"
          stroke="var(--primary)"
          strokeWidth="2.8"
          strokeLinecap="round"
          fill="none"
        />
      </svg>

      <span
        style={{
          fontFamily: "'Arial Black', 'Impact', sans-serif",
          fontSize: '19px',
          fontWeight: 900,
          letterSpacing: '3px',
          color: 'var(--primary)',
          lineHeight: 1,
          textTransform: 'uppercase',
        }}
      >
        NET
      </span>

      <span
        style={{
          fontFamily: "'Cairo', sans-serif",
          fontSize: '9.5px',
          fontWeight: 700,
          color: 'var(--primary)',
          letterSpacing: '0.3px',
          marginTop: '4px',
          whiteSpace: 'nowrap',
        }}
      >
        مزود خدمة الإنترنت
      </span>
    </div>
  );
}

/* ─────────────────────────────── Input Field Component ─────────────────────────────────────── */
function LabeledInput({ label, type, value, onChange, onKeyDown, onKeyUp, disabled, autoFocus, icon }) {
  const [focused, setFocused] = useState(false);

  return (
    <div
      style={{
        backgroundColor: '#edf2f9',
        borderRadius: '10px',
        padding: '8px 14px 10px',
        border: `1.5px solid ${focused ? '#7cb9f5' : 'transparent'}`,
        transition: 'border-color 0.2s, background 0.2s',
        position: 'relative',
      }}
    >
      <label
        style={{
          display: 'block',
          fontSize: '11px',
          fontWeight: 700,
          color: focused ? '#4a90d9' : '#94a3b8',
          textAlign: 'right',
          marginBottom: '3px',
          transition: 'color 0.2s',
          userSelect: 'none',
        }}
      >
        {label}
      </label>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', direction: 'rtl' }}>
        <input
          type={type}
          value={value}
          onChange={onChange}
          onKeyDown={onKeyDown}
          onKeyUp={onKeyUp}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          disabled={disabled}
          autoFocus={autoFocus}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            fontSize: '14px',
            fontWeight: 600,
            color: '#1e293b',
            fontFamily: 'inherit',
            padding: 0,
            textAlign: type === 'password' ? 'left' : 'right',
            direction: type === 'password' ? 'ltr' : 'rtl',
            letterSpacing: type === 'password' ? '2px' : 'normal',
          }}
        />
        {icon && (
          <span style={{ flexShrink: 0, display: 'flex', alignItems: 'center', color: '#94a3b8' }}>
            {icon}
          </span>
        )}
      </div>
    </div>
  );
}

/* ─────────────────────────────────── Main Component ────────────────────────────────────────── */
export default function LoginView() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isCapsLock, setIsCapsLock] = useState(false);

  const handleKeyEvent = (e) => {
    setIsCapsLock(!!(e.getModifierState && e.getModifierState('CapsLock')));
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

  const EyeToggle = (
    <button
      type="button"
      onClick={() => setShowPassword(!showPassword)}
      tabIndex={-1}
      style={{
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: 0,
        color: '#94a3b8',
        display: 'flex',
        alignItems: 'center',
        transition: 'color 0.2s',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.color = '#475569')}
      onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
    >
      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
    </button>
  );

  return (
    <>
      <style>{STYLE}</style>

      <div
        style={{
          minHeight: '100vh',
          width: '100%',
          backgroundColor: '#ffffff',
          display: 'flex',
          fontFamily: "'Cairo', sans-serif",
          position: 'relative',
          overflow: 'hidden',
          direction: 'rtl'
        }}
      >
        <div
          style={{
            flex: '0 0 44%',
            minWidth: '340px',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '40px 48px',
            position: 'relative',
            zIndex: 10,
          }}
        >
          <div style={{ position: 'absolute', top: '36px', right: '48px' }}>
            <HypernetLogo />
          </div>

          <div
            style={{
              width: '100%',
              maxWidth: '340px',
              animation: 'fadeIn 0.5s ease',
            }}
          >
            <h1
              style={{
                fontSize: '22px',
                fontWeight: 800,
                color: '#1e293b',
                marginBottom: '28px',
                letterSpacing: '-0.3px',
              }}
            >
              تسجيل الدخول للنظام
            </h1>

            {errorMsg && (
              <div
                style={{
                  background: '#fef2f2',
                  border: '1px solid #fecaca',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  marginBottom: '18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  color: '#dc2626',
                  fontSize: '13px',
                  fontWeight: 600,
                  animation: 'shake 0.3s ease',
                }}
              >
                <AlertTriangle size={16} style={{ flexShrink: 0 }} />
                <span style={{ flex: 1 }}>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '14px' }}>
                <LabeledInput
                  label="اسم المستخدم"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={isLoading}
                  autoFocus
                />
              </div>

              <div style={{ marginBottom: '6px' }}>
                <LabeledInput
                  label="كلمة المرور"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={handleKeyEvent}
                  onKeyUp={handleKeyEvent}
                  disabled={isLoading}
                  icon={EyeToggle}
                />
              </div>

              {isCapsLock && (
                <div
                  style={{
                    color: '#d97706',
                    fontSize: '12px',
                    fontWeight: 600,
                    marginBottom: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <AlertTriangle size={12} /> زر Caps Lock مفعل
                </div>
              )}

              <div style={{ height: '24px' }} />

              <button
                type="submit"
                disabled={isLoading}
                style={{
                  width: '100%',
                  height: '46px',
                  backgroundColor: '#1b2533',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '10px',
                  fontSize: '15px',
                  fontWeight: 700,
                  fontFamily: 'inherit',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'background-color 0.2s, transform 0.1s',
                  boxShadow: '0 2px 10px rgba(27, 37, 51, 0.22)',
                  opacity: isLoading ? 0.82 : 1,
                }}
                onMouseEnter={(e) => {
                  if (!isLoading) e.currentTarget.style.backgroundColor = '#0f172a';
                }}
                onMouseLeave={(e) => {
                  if (!isLoading) e.currentTarget.style.backgroundColor = '#1b2533';
                }}
                onMouseDown={(e) => {
                  if (!isLoading) e.currentTarget.style.transform = 'scale(0.99)';
                }}
                onMouseUp={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                {isLoading ? (
                  <>
                    <span
                      style={{
                        width: '16px',
                        height: '16px',
                        border: '2px solid rgba(255,255,255,0.35)',
                        borderTopColor: '#fff',
                        borderRadius: '50%',
                        display: 'inline-block',
                        animation: 'spin 0.8s linear infinite',
                      }}
                    />
                    <span>جاري التحقق...</span>
                  </>
                ) : (
                  <span>تسجيل الدخول</span>
                )}
              </button>
            </form>
          </div>
        </div>

        <div
          style={{
            flex: '1 1 56%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '40px',
            position: 'relative',
            backgroundColor: '#f8fafc',
          }}
        >
          <div
            style={{
              position: 'absolute',
              width: '500px',
              height: '500px',
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(220,235,250,0.6) 0%, rgba(248,250,252,0) 65%)',
              pointerEvents: 'none',
            }}
          />
        </div>
      </div>
    </>
  );
}
