import React from 'react';

interface EmptyStateProps {
  action?: React.ReactNode;
  description: string;
  icon: React.ElementType;
  title: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  action,
  description,
  icon: Icon,
  title,
}) => {
  return (
    <div className="zh-empty">
      <div className="zh-empty__icon">
        <Icon className="h-7 w-7" />
      </div>
      <h2 className="zh-empty__title">{title}</h2>
      <p className="zh-empty__description">{description}</p>
      {action}
    </div>
  );
};
