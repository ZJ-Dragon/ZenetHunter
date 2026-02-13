import React, { useEffect, useRef, useState } from 'react';
import { configService } from '../lib/services/config';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { OOBERegisterRequest, OOBEStatus } from '../types/config';
import { useTranslation } from 'react-i18next';

export const SetupWizard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<OOBEStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [formData, setFormData] = useState<OOBERegisterRequest>({
    username: '',
    password: '',
  });
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [timerReady, setTimerReady] = useState(false);
  const [hasScrolled, setHasScrolled] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(30);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const { t } = useTranslation();

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const s = await configService.getStatus();
        setStatus(s);
        if (s.first_run_completed) {
          navigate('/', { replace: true });
        }
      } catch (error) {
        console.error('Failed to load setup status', error);
      }
      setStatusLoading(false);
    };
    loadStatus();
  }, [navigate]);

  useEffect(() => {
    if (showDisclaimer) {
      setSecondsLeft(30);
      setTimerReady(false);
      timerRef.current = setInterval(() => {
        setSecondsLeft((prev) => {
          if (prev <= 1) {
            if (timerRef.current) clearInterval(timerRef.current);
            setTimerReady(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [showDisclaimer]);

  useEffect(() => {
    if (
      status &&
      status.admin_exists &&
      !status.first_run_completed &&
      isAuthenticated
    ) {
      setShowDisclaimer(true);
    }
  }, [status, isAuthenticated]);

  const handleScroll = () => {
    // Any scroll/wheel interaction counts as read acknowledgement
    setHasScrolled(true);
  };

  const handleRegister = async () => {
    const username = formData.username.trim();
    if (!username || username.toLowerCase() === 'admin') {
      toast.error(t('setup.adminReserved'));
      return;
    }
    setLoading(true);
    try {
      const result = await configService.register({ ...formData, username });
      login(result.access_token, { limitedAdmin: false });
      toast.success(t('setup.createAdmin'));
      setShowDisclaimer(true);
    } catch (error) {
      console.error(error);
      toast.error(t('login.resetFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async () => {
    setLoading(true);
    try {
      await configService.acknowledge({ acknowledged: true });
      toast.success(t('setup.modalTitle'));
      navigate('/', { replace: true });
    } catch (error) {
      console.error(error);
      toast.error(t('login.resetFailed'));
    } finally {
      setLoading(false);
    }
  };

  const readyToAcknowledge = hasScrolled && timerReady;
  const usernameTrimmed = formData.username.trim();
  const isAdminReserved = usernameTrimmed.toLowerCase() === 'admin';
  const registerDisabled =
    loading ||
    formData.password.length < 8 ||
    !usernameTrimmed ||
    (status?.admin_exists ?? false) ||
    isAdminReserved;

  if (statusLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-600" aria-label="Loading setup" />
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ backgroundColor: 'var(--winui-bg-primary)' }}>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-10 left-10 w-24 h-24 rounded-full blur-3xl opacity-20" style={{ backgroundColor: 'var(--winui-accent)' }}></div>
        <div className="absolute bottom-10 right-10 w-32 h-32 rounded-full blur-3xl opacity-15" style={{ backgroundColor: 'var(--winui-text-tertiary)' }}></div>
      </div>
      <div className="relative max-w-5xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <p className="text-sm font-semibold tracking-wide" style={{ color: 'var(--winui-accent)' }}>{t('setup.welcomeTag')}</p>
          <h1 className="mt-2 text-3xl sm:text-4xl font-bold" style={{ color: 'var(--winui-text-primary)' }}>{t('setup.welcomeTitle')}</h1>
          <p className="mt-3 text-base" style={{ color: 'var(--winui-text-secondary)' }}>
            {t('setup.welcomeDesc')}
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-6 items-start">
          <div className="md:col-span-3">
            <div className="card-winui shadow-xl rounded-2xl">
              <div className="px-6 py-4 border-b flex items-center gap-3" style={{ borderColor: 'var(--winui-border-subtle)' }}>
                <div className="h-10 w-10 rounded-full flex items-center justify-center font-semibold" style={{ backgroundColor: 'var(--winui-bg-tertiary)', color: 'var(--winui-accent)' }}>
                  1
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{t('setup.accountStep')}</p>
                  <p className="text-sm" style={{ color: 'var(--winui-text-secondary)' }}>{t('setup.accountSub')}</p>
                </div>
              </div>
              <div className="p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>{t('setup.username')}</label>
                  <input
                    type="text"
                    className="mt-1 input-winui block w-full"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    placeholder={t('setup.usernamePlaceholder')}
                    required
                  />
                  <p className="mt-1 text-xs text-gray-500">{t('setup.accountSub')}</p>
                  {isAdminReserved && (
                    <p className="mt-2 text-sm" style={{ color: '#d13438' }}>
                      {t('setup.adminReserved')}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>{t('setup.password')}</label>
                  <input
                    type="password"
                    className="mt-1 input-winui block w-full"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Enter a strong password"
                    required
                    minLength={8}
                  />
                  <p className="mt-2 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                    {t('setup.passwordNote')}
                  </p>
                  {status?.admin_exists && (
                    <p className="mt-2 text-sm" style={{ color: '#d13438' }}>
                      {t('setup.adminExists')}
                    </p>
                  )}
                </div>
                <div className="flex items-center justify-end">
                  <button
                    onClick={handleRegister}
                    disabled={registerDisabled}
                    className="btn-winui px-6 py-2 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? t('setup.creating') : t('setup.createAdmin')}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="md:col-span-2">
            <div className="card-winui shadow-lg rounded-2xl p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full flex items-center justify-center font-semibold" style={{ backgroundColor: 'var(--winui-bg-tertiary)', color: 'var(--winui-accent)' }}>
                  2
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{t('setup.safetyStep')}</p>
                  <p className="text-sm" style={{ color: 'var(--winui-text-secondary)' }}>{t('setup.safetySub')}</p>
                </div>
              </div>
              <p className="text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                {t('setup.safetyDesc')}
              </p>
              <ul className="text-sm space-y-1 list-disc list-inside" style={{ color: 'var(--winui-text-secondary)' }}>
                <li>{t('setup.safetyList1')}</li>
                <li>{t('setup.safetyList2')}</li>
                <li>{t('setup.safetyList3')}</li>
              </ul>
              <div className="rounded-lg p-4 text-sm" style={{ backgroundColor: 'var(--winui-bg-tertiary)', color: 'var(--winui-text-secondary)', border: '1px solid var(--winui-border-subtle)' }}>
                {t('setup.safetyInfo')}
              </div>
            </div>
          </div>
        </div>
      </div>

      {showDisclaimer && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center px-4"
          role="dialog"
          aria-modal="true"
          aria-label="Safety and Disclaimer"
          style={{ backgroundColor: 'rgba(0,0,0,0.4)' }}
        >
          <div className="rounded-2xl shadow-2xl max-w-3xl w-full outline-none overflow-hidden" style={{ backgroundColor: 'var(--winui-surface)', color: 'var(--winui-text-primary)' }}>
            <div className="p-6" style={{ backgroundColor: 'var(--winui-accent)' }}>
              <h2 className="text-xl font-semibold text-white">{t('setup.modalTitle')}</h2>
              <p className="text-sm text-indigo-50 mt-2">
                {t('setup.modalLead')}
              </p>
            </div>
            <div
              className="p-6 max-h-96 overflow-y-auto space-y-4 text-sm"
              onScroll={handleScroll}
              onWheel={handleScroll}
              ref={scrollRef}
              tabIndex={0}
              style={{ color: 'var(--winui-text-secondary)' }}
            >
              <div className="space-y-2">
                <p className="text-base font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{t('setup.modalPurpose')}</p>
                <p>{t('setup.modalPurposeDesc')}</p>
              </div>
              <div className="space-y-2">
                <p className="text-base font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{t('setup.modalResp')}</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>{t('setup.modalResp1')}</li>
                  <li>{t('setup.modalResp2')}</li>
                  <li>{t('setup.modalResp3')}</li>
                </ul>
              </div>
              <div className="space-y-2">
                <p className="text-base font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{t('setup.modalSafety')}</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>{t('setup.modalSafety1')}</li>
                  <li>{t('setup.modalSafety2')}</li>
                  <li>{t('setup.modalSafety3')}</li>
                </ul>
              </div>
              <p className="text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                {t('setup.modalFooterHint')}
              </p>
            </div>
            <div className="px-6 pb-6 pt-3 flex items-center justify-between border-t border-gray-200">
              <div className="text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                <div>
                  {t('setup.timerLabel')}: {timerReady ? t('setup.timerReady') : t('setup.timerRemaining', { seconds: secondsLeft })}
                </div>
                <div className="text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>{t('setup.modalFooterHint')}</div>
              </div>
              <button
                className="btn-winui px-6 py-2 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleAcknowledge}
                disabled={!readyToAcknowledge || loading || !isAuthenticated}
                autoFocus
              >
                {t('setup.iUnderstand')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
