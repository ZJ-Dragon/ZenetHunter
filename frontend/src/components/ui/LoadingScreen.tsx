import React from 'react';
import { Shield } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Surface } from './Surface';
import { Spinner } from './Spinner';

interface LoadingScreenProps {
  message?: string;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message,
}) => {
  const { t } = useTranslation();
  const resolvedMessage = message || t('loading.preparingWorkspace');

  return (
    <div className="zh-loading-screen">
      <Surface className="zh-loading-screen__panel" tone="raised">
        <div className="zh-brand" style={{ justifyContent: 'center' }}>
          <div className="zh-brand__mark">
            <Shield className="h-6 w-6" />
          </div>
          <div style={{ textAlign: 'left' }}>
            <p className="zh-kicker">{t('shell.brandTag')}</p>
            <h1 className="zh-brand__title">ZenetHunter</h1>
          </div>
        </div>
        <div
          style={{
            alignItems: 'center',
            color: 'var(--accent)',
            display: 'inline-flex',
            gap: '0.75rem',
            marginTop: '1.5rem',
          }}
        >
          <Spinner size="lg" />
          <span style={{ fontWeight: 600 }}>{resolvedMessage}</span>
        </div>
      </Surface>
    </div>
  );
};
