import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  ShieldCheck,
  UserRoundPlus,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { Button } from '../components/ui/Button';
import { Dialog } from '../components/ui/Dialog';
import { LoadingScreen } from '../components/ui/LoadingScreen';
import { Surface } from '../components/ui/Surface';
import { useAuth } from '../contexts/AuthContext';
import { configService } from '../lib/services/config';
import { OOBERegisterRequest, OOBEStatus } from '../types/config';

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
        const response = await configService.getStatus();
        setStatus(response);
        if (response.first_run_completed) {
          navigate('/', { replace: true });
        }
      } catch (error) {
        console.error('Failed to load setup status', error);
      } finally {
        setStatusLoading(false);
      }
    };

    loadStatus();
  }, [navigate]);

  useEffect(() => {
    if (!showDisclaimer) {
      return undefined;
    }

    setSecondsLeft(30);
    setTimerReady(false);

    timerRef.current = setInterval(() => {
      setSecondsLeft((previous) => {
        if (previous <= 1) {
          if (timerRef.current) {
            clearInterval(timerRef.current);
          }
          setTimerReady(true);
          return 0;
        }

        return previous - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
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
  }, [isAuthenticated, status]);

  const handleScroll = () => {
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
      if (typeof error === 'object' && error !== null && 'response' in error) {
        const errResp = error as { response?: { data?: { detail?: string } } };
        toast.error(errResp.response?.data?.detail || t('login.resetFailed'));
      } else {
        toast.error(t('login.resetFailed'));
      }
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
    return <LoadingScreen message="Preparing first-run experience..." />;
  }

  return (
    <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 max-w-3xl">
          <p className="zh-kicker">{t('setup.welcomeTag')}</p>
          <h1
            className="mt-3 text-4xl font-bold tracking-[-0.05em]"
            style={{ color: 'var(--text-primary)' }}
          >
            {t('setup.welcomeTitle')}
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7" style={{ color: 'var(--text-secondary)' }}>
            {t('setup.welcomeDesc')}
          </p>
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Surface className="p-8 lg:p-10" tone="raised">
            <div className="flex items-start justify-between gap-6">
              <div>
                <p className="zh-kicker">{t('setup.accountStep')}</p>
                <h2
                  className="mt-2 text-3xl font-semibold tracking-[-0.04em]"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {t('setup.createAdmin')}
                </h2>
                <p className="mt-3 text-sm leading-6" style={{ color: 'var(--text-secondary)' }}>
                  {t('setup.accountSub')}
                </p>
              </div>
              <div
                className="inline-flex h-14 w-14 items-center justify-center rounded-[1.2rem]"
                style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }}
              >
                <UserRoundPlus className="h-6 w-6" />
              </div>
            </div>

            <div className="mt-8 grid gap-5">
              <div>
                <label className="mb-2 block text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                  {t('setup.username')}
                </label>
                <input
                  className="zh-field"
                  onChange={(event) =>
                    setFormData({ ...formData, username: event.target.value })
                  }
                  placeholder={t('setup.usernamePlaceholder')}
                  required
                  type="text"
                  value={formData.username}
                />
                <p className="mt-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                  {t('setup.accountSub')}
                </p>
                {isAdminReserved ? (
                  <p className="mt-2 text-sm" style={{ color: 'var(--danger)' }}>
                    {t('setup.adminReserved')}
                  </p>
                ) : null}
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                  {t('setup.password')}
                </label>
                <input
                  className="zh-field"
                  minLength={8}
                  onChange={(event) =>
                    setFormData({ ...formData, password: event.target.value })
                  }
                  placeholder="Enter a strong password"
                  required
                  type="password"
                  value={formData.password}
                />
                <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {t('setup.passwordNote')}
                </p>
                {status?.admin_exists ? (
                  <p className="mt-2 text-sm" style={{ color: 'var(--danger)' }}>
                    {t('setup.adminExists')}
                  </p>
                ) : null}
              </div>

              <Surface className="p-5" tone="subtle">
                <p className="zh-kicker">{t('setup.safetyStep')}</p>
                <div className="mt-4 space-y-3">
                  {[t('setup.safetyList1'), t('setup.safetyList2'), t('setup.safetyList3')].map(
                    (item) => (
                      <div className="flex items-start gap-3" key={item}>
                        <CheckCircle2
                          className="mt-0.5 h-4 w-4 flex-shrink-0"
                          style={{ color: 'var(--success)' }}
                        />
                        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                          {item}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </Surface>

              <div className="flex justify-end">
                <Button
                  disabled={registerDisabled}
                  loading={loading}
                  onClick={handleRegister}
                  trailingIcon={!loading ? <ArrowRight className="h-4 w-4" /> : undefined}
                  type="button"
                >
                  {loading ? t('setup.creating') : t('setup.createAdmin')}
                </Button>
              </div>
            </div>
          </Surface>

          <div className="space-y-6">
            <Surface className="p-8" tone="raised">
              <div className="flex items-center gap-3">
                <div
                  className="inline-flex h-12 w-12 items-center justify-center rounded-[1.1rem]"
                  style={{ background: 'var(--success-soft)', color: 'var(--success)' }}
                >
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <p className="zh-kicker">{t('setup.safetyStep')}</p>
                  <h2 className="mt-1 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {t('setup.safetySub')}
                  </h2>
                </div>
              </div>
              <p className="mt-5 text-sm leading-7" style={{ color: 'var(--text-secondary)' }}>
                {t('setup.safetyDesc')}
              </p>
              <Surface className="mt-5 p-5" tone="subtle">
                <p className="text-sm leading-7" style={{ color: 'var(--text-secondary)' }}>
                  {t('setup.safetyInfo')}
                </p>
              </Surface>
            </Surface>

            <Surface className="p-8" tone="subtle">
              <p className="zh-kicker">Guidance</p>
              <div className="mt-5 space-y-4">
                <div className="flex items-start gap-3">
                  <Clock3 className="mt-0.5 h-5 w-5" style={{ color: 'var(--accent)' }} />
                  <div>
                    <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                      Timed acknowledgement
                    </p>
                    <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                      Review the safety notice for 30 seconds and scroll through it before the
                      primary console unlocks.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5" style={{ color: 'var(--warning)' }} />
                  <div>
                    <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                      Restricted networks only
                    </p>
                    <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                      The active defense surface is intentionally separated from setup so you can
                      confirm policy before using any disruptive action.
                    </p>
                  </div>
                </div>
              </div>
            </Surface>
          </div>
        </div>
      </div>

      <Dialog
        description={t('setup.modalLead')}
        footer={
          <>
            <div>
              <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('setup.timerLabel')}:{' '}
                {timerReady
                  ? t('setup.timerReady')
                  : t('setup.timerRemaining', { seconds: secondsLeft })}
              </p>
              <p className="mt-1 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                {t('setup.modalFooterHint')}
              </p>
            </div>
            <Button
              disabled={!readyToAcknowledge || loading || !isAuthenticated}
              loading={loading}
              onClick={handleAcknowledge}
              type="button"
            >
              {t('setup.iUnderstand')}
            </Button>
          </>
        }
        open={showDisclaimer}
        title={t('setup.modalTitle')}
      >
        <div
          className="max-h-[22rem] space-y-6 overflow-y-auto pr-2"
          onScroll={handleScroll}
          onWheel={handleScroll}
          ref={scrollRef}
          tabIndex={0}
        >
          <Surface className="p-5" tone="subtle">
            <p className="zh-kicker">{t('setup.modalPurpose')}</p>
            <p className="mt-3 text-sm leading-7" style={{ color: 'var(--text-secondary)' }}>
              {t('setup.modalPurposeDesc')}
            </p>
          </Surface>
          <Surface className="p-5" tone="subtle">
            <p className="zh-kicker">{t('setup.modalResp')}</p>
            <ul
              className="mt-3 space-y-2 text-sm leading-7"
              style={{ color: 'var(--text-secondary)' }}
            >
              <li>{t('setup.modalResp1')}</li>
              <li>{t('setup.modalResp2')}</li>
              <li>{t('setup.modalResp3')}</li>
            </ul>
          </Surface>
          <Surface className="p-5" tone="subtle">
            <p className="zh-kicker">{t('setup.modalSafety')}</p>
            <ul
              className="mt-3 space-y-2 text-sm leading-7"
              style={{ color: 'var(--text-secondary)' }}
            >
              <li>{t('setup.modalSafety1')}</li>
              <li>{t('setup.modalSafety2')}</li>
              <li>{t('setup.modalSafety3')}</li>
            </ul>
          </Surface>
        </div>
      </Dialog>
    </div>
  );
};
