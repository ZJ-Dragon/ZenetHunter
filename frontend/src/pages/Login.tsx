import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';
import { Lock, User, ShieldAlert } from 'lucide-react';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('admin');  // Pre-fill default username
  const [password, setPassword] = useState('');  // Don't pre-fill password for security
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Sending as x-www-form-urlencoded as per OAuth2 standard in FastAPI
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await api.post('/auth/login', params.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;
      login(access_token);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (typeof err === 'object' && err !== null && 'response' in err) {
        // Use type assertion to access error response
        const errorResponse = err as { response?: { data?: { detail?: string } } };
        setError(
          errorResponse.response?.data?.detail ||
            'Login failed. Please check your credentials.'
        );
      } else {
        setError('Login failed. Please check your credentials.');
      }
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: 'var(--winui-bg-primary)' }}>
      <div className="max-w-md w-full card-winui overflow-hidden">
        <div className="p-6 text-center" style={{ backgroundColor: 'var(--winui-accent)', color: '#ffffff' }}>
          <div className="flex justify-center mb-4">
            <div className="p-3 rounded-full" style={{ backgroundColor: '#ffffff' }}>
              <ShieldAlert className="w-8 h-8" style={{ color: 'var(--winui-accent)' }} />
            </div>
          </div>
          <h1 className="text-2xl font-semibold text-white">ZenetHunter</h1>
          <p className="mt-2 text-sm" style={{ color: 'rgba(255, 255, 255, 0.9)' }}>Local Network Defense System</p>
        </div>

        <div className="p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 text-sm rounded-lg" style={{ backgroundColor: 'rgba(209, 52, 56, 0.1)', color: '#d13438', border: '1px solid rgba(209, 52, 56, 0.3)' }}>
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: 'var(--winui-text-primary)' }}>Username</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5" style={{ color: 'var(--winui-text-tertiary)' }} />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="input-winui block w-full pr-3 py-2"
                  style={{ paddingLeft: '42px' }}
                  placeholder="admin"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: 'var(--winui-text-primary)' }}>Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5" style={{ color: 'var(--winui-text-tertiary)' }} />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-winui block w-full pr-3 py-2"
                  style={{ paddingLeft: '42px' }}
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-winui w-full flex justify-center py-2 px-4 text-sm font-medium text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>

            <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--winui-border-subtle)' }}>
              <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(0, 120, 212, 0.1)', border: '1px solid rgba(0, 120, 212, 0.3)' }}>
                <p className="text-xs font-semibold mb-1" style={{ color: 'var(--winui-accent)' }}>首次使用？</p>
                <p className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>
                  管理员账户由首次启动时创建，请使用您设定的凭据登录。
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--winui-text-tertiary)' }}>
                  如果尚未完成初次设置，请返回 Setup 页面完成注册和安全确认。
                </p>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
