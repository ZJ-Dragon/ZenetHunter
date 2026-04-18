import React from 'react';
import { clsx } from 'clsx';

type SurfaceTone = 'default' | 'raised' | 'subtle' | 'inset' | 'danger';

interface SurfaceProps extends React.HTMLAttributes<HTMLDivElement> {
  tone?: SurfaceTone;
}

export const Surface: React.FC<SurfaceProps> = ({
  className,
  tone = 'default',
  ...props
}) => {
  return (
    <div
      className={clsx(
        'zh-surface',
        tone !== 'default' && `zh-surface--${tone}`,
        className
      )}
      {...props}
    />
  );
};
