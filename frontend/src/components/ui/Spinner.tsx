import React from 'react';
import { clsx } from 'clsx';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  className,
}) => {
  return (
    <span
      aria-hidden="true"
      className={clsx('zh-spinner', `zh-spinner--${size}`, className)}
    />
  );
};
