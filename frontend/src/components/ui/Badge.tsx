import React from 'react';
import { clsx } from 'clsx';

type BadgeTone = 'neutral' | 'accent' | 'success' | 'warning' | 'danger';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  className,
  tone = 'neutral',
  ...props
}) => {
  return (
    <span className={clsx('zh-badge', `zh-badge--${tone}`, className)} {...props}>
      {children}
    </span>
  );
};
