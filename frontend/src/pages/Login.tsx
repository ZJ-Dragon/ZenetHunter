import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';
import {
  ArrowRight,
  CheckCircle2,
  KeyRound,
  Lock,
  ShieldAlert,
  User,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Surface } from '../components/ui/Surface';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

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
      const isLimitedAdmin = username === 'admin' && password === 'zenethunter';
      login(access_token, { limitedAdmin: isLimitedAdmin });
      const target = isLimitedAdmin ? '/settings' : from;
      navigate(target, { replace: true });
    } catch (err: unknown) {
      if (typeof err === 'object' && err !== null && 'response' in err) {
        // Use type assertion to access error response
        const errorResponse = err as { response?: { data?: { detail?: string } } };
        setError(
          errorResponse.response?.data?.detail ||
            t('login.resetFailed')
        );
      } else {
        setError(t('login.resetFailed'));
      }
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl items-center">
        <div className="grid w-full gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Surface className="overflow-hidden p-8 lg:p-10" tone="raised">
            <div className="zh-hero-grid h-full">
              <div className="flex flex-wrap items-center gap-3">
                <Badge tone="accent">{t('login.workspaceTag')}</Badge>
                <Badge tone="success">{t('login.sessionTag')}</Badge>
              </div>
              <div>
                <div
                  className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-[1.5rem]"
                  style={{
                    background:
                      'linear-gradient(180deg, var(--accent-soft), rgba(255,255,255,0.12))',
                    color: 'var(--accent)',
                  }}
                >
                  <ShieldAlert className="h-8 w-8" />
                </div>
                <p className="zh-kicker">{t('login.kicker')}</p>
                <h1
                  className="mt-2 text-4xl font-bold tracking-[-0.04em]"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {t('login.title')}
                </h1>
                <p
                  className="mt-4 max-w-xl text-base leading-7"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  {t('login.subtitle')}
                </p>
              </div>
              <div className="zh-detail-grid">
                <Surface className="zh-detail-card" tone="subtle">
                  <p className="zh-detail-card__label">{t('login.accessLabel')}</p>
                  <p className="zh-detail-card__value text-sm font-semibold">
                    {t('login.accessDesc')}
                  </p>
                </Surface>
                <Surface className="zh-detail-card" tone="subtle">
                  <p className="zh-detail-card__label">{t('login.firstRunLabel')}</p>
                  <p className="zh-detail-card__value text-sm font-semibold">
                    {t('login.firstRunDesc')}
                  </p>
                </Surface>
              </div>
              <Surface className="p-5" tone="subtle">
                <p className="zh-kicker">{t('login.benefitsKicker')}</p>
                <div className="mt-4 space-y-3">
                  {[
                    t('login.benefit1'),
                    t('login.benefit2'),
                    t('login.benefit3'),
                  ].map((item) => (
                    <div className="flex items-start gap-3" key={item}>
                      <CheckCircle2
                        className="mt-0.5 h-4 w-4 flex-shrink-0"
                        style={{ color: 'var(--success)' }}
                      />
                      <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                        {item}
                      </span>
                    </div>
                  ))}
                </div>
              </Surface>
            </div>
          </Surface>

          <Surface className="p-8 lg:p-10" tone="raised">
            <div className="flex items-center gap-3">
              <div
                className="inline-flex h-12 w-12 items-center justify-center rounded-[1.1rem]"
                style={{ background: 'var(--surface-inset)', color: 'var(--accent)' }}
              >
                <KeyRound className="h-5 w-5" />
              </div>
              <div>
                <p className="zh-kicker">{t('login.authKicker')}</p>
                <h2 className="mt-1 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                  {t('login.signIn')}
                </h2>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              {error ? (
                <Surface className="p-4 text-sm" tone="danger">
                  {error}
                </Surface>
              ) : null}

              <div>
                <label
                  className="mb-2 block text-sm font-medium"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {t('login.username')}
                </label>
                <div className="zh-field-wrap">
                  <User className="zh-field-icon h-4 w-4" />
                  <input
                    className="zh-field"
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder={t('login.username')}
                    required
                    type="text"
                    value={username}
                  />
                </div>
              </div>

              <div>
                <label
                  className="mb-2 block text-sm font-medium"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {t('login.password')}
                </label>
                <div className="zh-field-wrap">
                  <Lock className="zh-field-icon h-4 w-4" />
                  <input
                    className="zh-field"
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t('login.password')}
                    required
                    type="password"
                    value={password}
                  />
                </div>
              </div>

              <Button
                fullWidth
                loading={isLoading}
                trailingIcon={!isLoading ? <ArrowRight className="h-4 w-4" /> : undefined}
                type="submit"
              >
                {isLoading ? t('login.signingIn') : t('login.signIn')}
              </Button>
            </form>

            <Surface className="mt-6 p-4" tone="subtle">
              <p className="zh-kicker">{t('login.firstUse')}</p>
              <p className="mt-2 text-sm leading-6" style={{ color: 'var(--text-secondary)' }}>
                {t('login.firstUseHint')}
              </p>
              <Button
                className="mt-4"
                onClick={() => navigate('/setup')}
                trailingIcon={<ArrowRight className="h-4 w-4" />}
                type="button"
                variant="secondary"
              >
                {t('login.setupLink')}
              </Button>
            </Surface>

            {from !== '/' ? (
              <p className="mt-6 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                {t('login.returnTo', { path: from })}
              </p>
            ) : null}
          </Surface>
        </div>
      </div>
    </div>
  );
};
