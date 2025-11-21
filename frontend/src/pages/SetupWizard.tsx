import React, { useState } from 'react';
import { WizardLayout } from '../components/layout/WizardLayout';
import { configService } from '../lib/services/config';
import { OOBESetupRequest } from '../types/config';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

export const SetupWizard: React.FC = () => {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const [formData, setFormData] = useState<OOBESetupRequest>({
    target_subnets: [],
    scan_interval: 300,
    default_policy: 'monitor',
    admin_password: '',
  });

  const handleNext = async () => {
    if (step < 2) {
      setStep(step + 1);
    } else {
      // Final Step - Submit
      setLoading(true);
      try {
        await configService.setup(formData);
        toast.success('Setup completed successfully!');
        navigate('/login');
      } catch (error) {
        console.error(error);
        toast.error('Failed to complete setup');
      } finally {
        setLoading(false);
      }
    }
  };

  const renderStepContent = () => {
    switch (step) {
      case 0:
        return (
          <div className="space-y-6">
            <h4 className="font-medium text-gray-900">Set Admin Password</h4>
            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                value={formData.admin_password}
                onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
              />
              <p className="mt-2 text-sm text-gray-500">Secure your ZenetHunter instance.</p>
            </div>
          </div>
        );
      case 1:
        return (
          <div className="space-y-6">
            <h4 className="font-medium text-gray-900">Network Configuration</h4>
            <div>
              <label className="block text-sm font-medium text-gray-700">Target Subnets (comma separated)</label>
              <input
                type="text"
                placeholder="192.168.1.0/24"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                value={formData.target_subnets.join(', ')}
                onChange={(e) => setFormData({ ...formData, target_subnets: e.target.value.split(',').map(s => s.trim()) })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Scan Interval (seconds)</label>
              <input
                type="number"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
                value={formData.scan_interval}
                onChange={(e) => setFormData({ ...formData, scan_interval: parseInt(e.target.value) })}
              />
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <h4 className="font-medium text-gray-900">Security Policy</h4>
            <div>
              <label className="block text-sm font-medium text-gray-700">Default Action for New Devices</label>
              <select
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm rounded-md"
                value={formData.default_policy}
                onChange={(e) => setFormData({ ...formData, default_policy: e.target.value as 'monitor' | 'block_unknown' })}
              >
                <option value="monitor">Monitor Only (Recommended)</option>
                <option value="block_unknown">Auto-Block Unknown</option>
              </select>
              <p className="mt-2 text-sm text-gray-500">
                "Monitor Only" will just log new devices. "Auto-Block" will immediately interfere with unrecognized devices.
              </p>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  const titles = ['Admin Security', 'Network Scan', 'Default Policy'];
  const descs = [
    'Create a strong password for the admin account.',
    'Configure which networks ZenetHunter should monitor.',
    'Decide how the system handles unknown devices.'
  ];

  return (
    <WizardLayout
      currentStep={step}
      totalSteps={3}
      title={titles[step]}
      description={descs[step]}
      onNext={handleNext}
      onBack={() => setStep(step - 1)}
      isNextLoading={loading}
      nextLabel={step === 2 ? 'Finish Setup' : 'Next'}
    >
      {renderStepContent()}
    </WizardLayout>
  );
};
