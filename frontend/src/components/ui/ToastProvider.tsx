import React from 'react';
import { Toaster } from 'react-hot-toast';

export const ToastProvider: React.FC = () => {
  return (
    <Toaster
      position="top-right"
      reverseOrder={false}
      toastOptions={{
        success: {
          style: {
            background: '#ecfdf5',
            color: '#065f46',
            border: '1px solid #a7f3d0',
          },
        },
        error: {
          style: {
            background: '#fef2f2',
            color: '#991b1b',
            border: '1px solid #fecaca',
          },
        },
        duration: 4000,
      }}
    />
  );
};

