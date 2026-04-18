import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '../components/ui/Button';
import { Surface } from '../components/ui/Surface';

export const NotFound: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen px-4 py-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-3xl items-center justify-center">
        <Surface className="w-full px-8 py-10 text-center" tone="raised">
          <div
            className="mx-auto mb-6 inline-flex h-20 w-20 items-center justify-center rounded-[1.75rem]"
            style={{ background: 'var(--warning-soft)', color: 'var(--warning)' }}
          >
            <AlertTriangle className="h-10 w-10" />
          </div>
          <p className="zh-kicker">Navigation Error</p>
          <h1
            className="mt-3 text-5xl font-bold tracking-[-0.05em]"
            style={{ color: 'var(--text-primary)' }}
          >
            {t('notfound.code')}
          </h1>
          <h2 className="mt-3 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            {t('notfound.title')}
          </h2>
          <p
            className="mx-auto mt-4 max-w-xl text-base leading-7"
            style={{ color: 'var(--text-secondary)' }}
          >
            {t('notfound.message')}
          </p>
          <div className="mt-8 flex justify-center">
            <Link to="/">
              <Button>{t('notfound.back')}</Button>
            </Link>
          </div>
        </Surface>
      </div>
    </div>
  );
};
