import React from 'react';
import { Toaster } from 'react-hot-toast';

export const ToastProvider: React.FC = () => {
  return (
    <Toaster
      position="top-right"
      reverseOrder={false}
      toastOptions={{
        style: {
          background: 'var(--surface-raised)',
          border: '1px solid var(--border)',
          borderRadius: '16px',
          boxShadow: 'var(--shadow-md)',
          color: 'var(--text-primary)',
          padding: '14px 16px',
        },
        success: {
          style: {
            background: 'var(--surface-raised)',
            color: 'var(--success)',
            border: '1px solid rgba(15, 123, 15, 0.2)',
          },
        },
        error: {
          style: {
            background: 'var(--surface-raised)',
            color: 'var(--danger)',
            border: '1px solid rgba(196, 43, 28, 0.22)',
          },
        },
        duration: 4000,
      }}
    />
  );
};
