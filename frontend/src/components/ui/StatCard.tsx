import React from 'react';
import { Surface } from './Surface';

interface StatCardProps {
  icon: React.ElementType;
  label: string;
  tone?: string;
  value: React.ReactNode;
  hint?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  hint,
  icon: Icon,
  label,
  tone,
  value,
}) => {
  return (
    <Surface className="zh-stat-card" tone="raised">
      <div>
        <p className="zh-stat-card__label">{label}</p>
        <p className="zh-stat-card__value">{value}</p>
        {hint ? <p className="zh-stat-card__hint">{hint}</p> : null}
      </div>
      <div className="zh-stat-card__icon" style={tone ? { color: tone } : undefined}>
        <Icon className="h-6 w-6" />
      </div>
    </Surface>
  );
};
