import React, { useEffect, useRef, useState } from 'react';
import { WizardLayout } from '../components/layout/WizardLayout';
import { configService } from '../lib/services/config';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { OOBERegisterRequest, OOBEStatus } from '../types/config';

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
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();

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
    if (!scrollRef.current) return;
    const { scrollTop, clientHeight, scrollHeight } = scrollRef.current;
    if (scrollTop + clientHeight >= scrollHeight - 8) {
      setHasScrolled(true);
    }
  };

  const handleRegister = async () => {
    setLoading(true);
    try {
      const result = await configService.register(formData);
      login(result.access_token);
      toast.success('Admin account created. Please review the safety notice.');
      setShowDisclaimer(true);
    } catch (error) {
      console.error(error);
      toast.error('Failed to create admin account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async () => {
    setLoading(true);
    try {
      await configService.acknowledge({ acknowledged: true });
      toast.success('Safety notice acknowledged. Welcome!');
      navigate('/', { replace: true });
    } catch (error) {
      console.error(error);
      toast.error('Failed to complete acknowledgment. Please retry.');
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
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: 'var(--winui-bg-primary)' }}>
      <div className="max-w-lg w-full">
        <WizardLayout
          currentStep={0}
          totalSteps={1}
          title="First-time Setup"
          description="Create an admin account to begin using ZenetHunter."
          onNext={handleRegister}
          onBack={undefined}
          isNextLoading={loading}
          nextLabel="Create Admin"
          isNextDisabled={
            loading ||
            formData.password.length < 8 ||
            !formData.username ||
            (status?.admin_exists ?? false)
          }
        >
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Admin Username</label>
              <input
                type="text"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="admin"
                required
              />
              <p className="mt-1 text-xs text-gray-500">Choose a unique admin username.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Admin Password</label>
              <input
                type="password"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Enter a strong password"
                required
                minLength={8}
              />
              <p className="mt-2 text-sm text-gray-500">
                Password is stored securely using modern hashing. Minimum 8 characters.
              </p>
              {status?.admin_exists && (
                <p className="mt-2 text-sm text-red-600">
                  An admin already exists. Please contact the administrator to continue.
                </p>
              )}
            </div>
          </div>
        </WizardLayout>
      </div>

      {showDisclaimer && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center px-4"
          role="dialog"
          aria-modal="true"
          aria-label="Safety and Disclaimer"
          style={{ backgroundColor: 'rgba(0,0,0,0.4)' }}
        >
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full outline-none">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Safety &amp; Disclaimer</h2>
              <p className="text-sm text-gray-600 mt-2">
                Please read the following notice carefully before proceeding.
              </p>
            </div>
            <div
              className="p-6 max-h-80 overflow-y-auto space-y-4 text-sm text-gray-700"
              onScroll={handleScroll}
              ref={scrollRef}
              tabIndex={0}
            >
              <p>
                ZenetHunter operates solely within authorized, private network environments under oversight.
                Its capabilities are intended for defense, monitoring, and policy enforcement to mitigate misuse and data loss.
              </p>
              <p>
                By proceeding, you confirm you are authorized to administer this environment, and you will comply with
                applicable laws, internal security policies, and acceptable use guidelines.
              </p>
              <p>
                Some features may interact with networked devices. Use them responsibly and ensure affected parties are informed
                per your organizational policy.
              </p>
              <p>
                If you do not agree, close this application now. Otherwise, scroll to the end and acknowledge after the timer expires.
              </p>
              <p className="text-xs text-gray-500">
                Implementation details of sensitive capabilities are intentionally omitted in this notice.
              </p>
            </div>
            <div className="px-6 pb-6 pt-3 flex items-center justify-between border-t border-gray-200">
              <div className="text-sm text-gray-600">
                <div>Scroll required: {hasScrolled ? 'Done' : 'Pending'}</div>
                <div>Timer: {timerReady ? 'Ready' : `${secondsLeft}s remaining`}</div>
              </div>
              <button
                className="btn-winui px-6 py-2 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleAcknowledge}
                disabled={!readyToAcknowledge || loading || !isAuthenticated}
                autoFocus
              >
                I Understand
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
