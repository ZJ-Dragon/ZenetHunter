import React from 'react';
import { X } from 'lucide-react';
import { Button } from './Button';

interface DialogProps {
  children: React.ReactNode;
  description?: string;
  footer?: React.ReactNode;
  onClose?: () => void;
  open: boolean;
  title: string;
}

export const Dialog: React.FC<DialogProps> = ({
  children,
  description,
  footer,
  onClose,
  open,
  title,
}) => {
  if (!open) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="zh-modal-backdrop"
      onClick={onClose}
      role="dialog"
    >
      <div className="zh-modal" onClick={(event) => event.stopPropagation()}>
        <div
          className="flex items-start justify-between gap-4 p-6"
          style={{ borderBottom: '1px solid var(--border)' }}
        >
          <div>
            <p className="zh-kicker">Attention Required</p>
            <h2 className="mt-2 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
              {title}
            </h2>
            {description ? (
              <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                {description}
              </p>
            ) : null}
          </div>
          {onClose ? (
            <Button
              aria-label="Close dialog"
              onClick={onClose}
              size="icon"
              variant="ghost"
            >
              <X className="h-5 w-5" />
            </Button>
          ) : null}
        </div>
        <div className="p-6">{children}</div>
        {footer ? (
          <div
            className="flex flex-wrap items-center justify-between gap-3 px-6 pb-6"
            style={{ borderTop: '1px solid var(--border)', paddingTop: '1.25rem' }}
          >
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
};
