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
    username: 'admin',
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
    setLoading(true);
    try {
      const result = await configService.register(formData);
      login(result.access_token);
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

  if (statusLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-600" aria-label="Loading setup" />
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ background: 'radial-gradient(circle at 20% 20%, rgba(99,102,241,0.15), transparent 35%), radial-gradient(circle at 80% 0%, rgba(59,130,246,0.18), transparent 30%), linear-gradient(135deg, #f5f7fb 0%, #edf2ff 100%)' }}>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-10 left-10 w-24 h-24 bg-indigo-200 rounded-full blur-3xl opacity-40"></div>
        <div className="absolute bottom-10 right-10 w-32 h-32 bg-blue-200 rounded-full blur-3xl opacity-30"></div>
      </div>
      <div className="relative max-w-5xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <p className="text-sm font-semibold text-indigo-600 tracking-wide">{t('setup.welcomeTag')}</p>
          <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight">{t('setup.welcomeTitle')}</h1>
          <p className="mt-3 text-base text-gray-600">
            {t('setup.welcomeDesc')}
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-6 items-start">
          <div className="md:col-span-3">
            <div className="bg-white shadow-xl rounded-2xl border border-indigo-100">
              <div className="px-6 py-4 border-b border-indigo-50 flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-semibold">
                  1
                </div>
                <div>
                  <p className="text-sm font-semibold text-indigo-700">{t('setup.accountStep')}</p>
                  <p className="text-sm text-gray-600">{t('setup.accountSub')}</p>
                </div>
              </div>
              <div className="p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('setup.username')}</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    placeholder="admin"
                    required
                  />
                  <p className="mt-1 text-xs text-gray-500">{t('setup.accountSub')}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('setup.password')}</label>
                  <input
                    type="password"
                    className="mt-1 block w-full border-gray-300 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Enter a strong password"
                    required
                    minLength={8}
                  />
                  <p className="mt-2 text-sm text-gray-500">
                    {t('setup.passwordNote')}
                  </p>
                  {status?.admin_exists && (
                    <p className="mt-2 text-sm text-red-600">
                      {t('setup.adminExists')}
                    </p>
                  )}
                </div>
                <div className="flex items-center justify-end">
                  <button
                    onClick={handleRegister}
                    disabled={
                      loading ||
                      formData.password.length < 8 ||
                      !formData.username ||
                      (status?.admin_exists ?? false)
                    }
                    className="btn-winui px-6 py-2 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? t('setup.creating') : t('setup.createAdmin')}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="md:col-span-2">
            <div className="bg-white border border-gray-200 shadow-lg rounded-2xl p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold">
                  2
                </div>
                <div>
                  <p className="text-sm font-semibold text-blue-700">{t('setup.safetyStep')}</p>
                  <p className="text-sm text-gray-600">{t('setup.safetySub')}</p>
                </div>
              </div>
              <p className="text-sm text-gray-600">
                {t('setup.safetyDesc')}
              </p>
              <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                <li>{t('setup.safetyList1')}</li>
                <li>{t('setup.safetyList2')}</li>
                <li>{t('setup.safetyList3')}</li>
              </ul>
              <div className="rounded-lg bg-indigo-50 border border-indigo-100 p-4 text-sm text-indigo-800">
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
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full outline-none overflow-hidden">
            <div className="p-6 bg-gradient-to-r from-indigo-600 to-blue-500">
              <h2 className="text-xl font-semibold text-white">{t('setup.modalTitle')}</h2>
              <p className="text-sm text-indigo-50 mt-2">
                {t('setup.modalLead')}
              </p>
            </div>
            <div
              className="p-6 max-h-96 overflow-y-auto space-y-4 text-sm text-gray-700"
              onScroll={handleScroll}
              onWheel={handleScroll}
              ref={scrollRef}
              tabIndex={0}
            >
              <div className="space-y-2">
                <p className="text-base font-semibold text-gray-900">{t('setup.modalPurpose')}</p>
                <p>{t('setup.modalPurposeDesc')}</p>
              </div>
              <div className="space-y-2">
                <p className="text-base font-semibold text-gray-900">{t('setup.modalResp')}</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>{t('setup.modalResp1')}</li>
                  <li>{t('setup.modalResp2')}</li>
                  <li>{t('setup.modalResp3')}</li>
                </ul>
              </div>
              <div className="space-y-2">
                <p className="text-base font-semibold text-gray-900">{t('setup.modalSafety')}</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>{t('setup.modalSafety1')}</li>
                  <li>{t('setup.modalSafety2')}</li>
                  <li>{t('setup.modalSafety3')}</li>
                </ul>
              </div>
              <p className="text-xs text-gray-500">
                {t('setup.modalFooterHint')}
              </p>
            </div>
            <div className="px-6 pb-6 pt-3 flex items-center justify-between border-t border-gray-200">
              <div className="text-sm text-gray-700">
                <div>
                  {t('setup.timerLabel')}: {timerReady ? t('setup.timerReady') : t('setup.timerRemaining', { seconds: secondsLeft })}
                </div>
                <div className="text-xs text-gray-500">{t('setup.modalFooterHint')}</div>
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
