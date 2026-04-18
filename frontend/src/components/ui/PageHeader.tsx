import React from 'react';

interface PageHeaderProps {
  eyebrow?: string;
  icon?: React.ElementType;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  actions,
  eyebrow,
  icon: Icon,
  subtitle,
  title,
}) => {
  return (
    <div className="zh-page-header">
      <div className="zh-page-header__content">
        {Icon ? (
          <div className="zh-page-header__icon">
            <Icon className="h-6 w-6" />
          </div>
        ) : null}
        <div>
          {eyebrow ? <p className="zh-page-header__eyebrow">{eyebrow}</p> : null}
          <h1 className="zh-page-header__title">{title}</h1>
          {subtitle ? <p className="zh-page-header__subtitle">{subtitle}</p> : null}
        </div>
      </div>
      {actions ? <div className="zh-page-header__actions">{actions}</div> : null}
    </div>
  );
};
