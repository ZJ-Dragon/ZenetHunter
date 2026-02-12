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
    // Any scroll/wheel interaction counts as read acknowledgement
    setHasScrolled(true);
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
    <div className="min-h-screen relative overflow-hidden" style={{ background: 'radial-gradient(circle at 20% 20%, rgba(99,102,241,0.15), transparent 35%), radial-gradient(circle at 80% 0%, rgba(59,130,246,0.18), transparent 30%), linear-gradient(135deg, #f5f7fb 0%, #edf2ff 100%)' }}>
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-10 left-10 w-24 h-24 bg-indigo-200 rounded-full blur-3xl opacity-40"></div>
        <div className="absolute bottom-10 right-10 w-32 h-32 bg-blue-200 rounded-full blur-3xl opacity-30"></div>
      </div>
      <div className="relative max-w-5xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <p className="text-sm font-semibold text-indigo-600 tracking-wide">Welcome to ZenetHunter</p>
          <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight">First-time Setup</h1>
          <p className="mt-3 text-base text-gray-600">
            Create your administrator account to secure the console. You’ll review a safety notice before continuing.
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
                  <p className="text-sm font-semibold text-indigo-700">Account</p>
                  <p className="text-sm text-gray-600">Set up admin credentials</p>
                </div>
              </div>
              <div className="p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Admin Username</label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
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
                    className="mt-1 block w-full border-gray-300 rounded-lg shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Enter a strong password"
                    required
                    minLength={8}
                  />
                  <p className="mt-2 text-sm text-gray-500">
                    Passwords are stored with modern hashing. Minimum 8 characters.
                  </p>
                  {status?.admin_exists && (
                    <p className="mt-2 text-sm text-red-600">
                      An admin already exists. Please contact the administrator to continue.
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
                    {loading ? 'Creating...' : 'Create Admin'}
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
                  <p className="text-sm font-semibold text-blue-700">Safety Notice</p>
                  <p className="text-sm text-gray-600">Acknowledgement required</p>
                </div>
              </div>
              <p className="text-sm text-gray-600">
                After creating the admin, you must read and acknowledge the safety disclaimer. You’ll need to scroll the notice and wait 30 seconds before continuing.
              </p>
              <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                <li>Operate only on authorized networks.</li>
                <li>Use disruptive actions responsibly.</li>
                <li>Close the app if you do not agree.</li>
              </ul>
              <div className="rounded-lg bg-indigo-50 border border-indigo-100 p-4 text-sm text-indigo-800">
                The setup will return you to the dashboard after you accept the notice.
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
              <h2 className="text-xl font-semibold text-white">Safety &amp; Disclaimer</h2>
              <p className="text-sm text-indigo-50 mt-2">
                Please review this notice before using ZenetHunter in your environment.
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
                <p className="text-base font-semibold text-gray-900">Purpose</p>
                <p>
                  ZenetHunter is designed for authorized, private networks to improve visibility and mitigate misuse.
                  Capabilities focus on monitoring, policy enforcement, and protective actions under appropriate oversight.
                </p>
              </div>
              <div className="space-y-2">
                <p className="text-base font-semibold text-gray-900">Your responsibilities</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Operate only with proper authorization and within approved network segments.</li>
                  <li>Follow applicable laws, internal security policies, and acceptable use guidelines.</li>
                  <li>Use disruptive features responsibly; notify stakeholders per your policy.</li>
                </ul>
              </div>
              <div className="space-y-2">
                <p className="text-base font-semibold text-gray-900">Safety notes</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Some actions interact with devices on the network; review before execution.</li>
                  <li>Logging is retained locally; avoid including sensitive personal data.</li>
                  <li>If you disagree with these terms, close the application now.</li>
                </ul>
              </div>
              <p className="text-xs text-gray-500">
                Implementation details of sensitive capabilities are intentionally omitted from this notice.
              </p>
            </div>
            <div className="px-6 pb-6 pt-3 flex items-center justify-between border-t border-gray-200">
              <div className="text-sm text-gray-700">
                <div>Timer: {timerReady ? 'Ready' : `${secondsLeft}s remaining`}</div>
                <div className="text-xs text-gray-500">Use scroll or mouse wheel to confirm you have read this notice.</div>
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
