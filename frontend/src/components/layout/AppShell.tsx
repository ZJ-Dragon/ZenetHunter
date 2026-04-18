import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  Network,
  Shield,
  Settings,
  LogOut,
  Menu,
  X,
  Activity,
  Terminal,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { Button } from '../ui/Button';
import { Surface } from '../ui/Surface';

const NavItem: React.FC<{
  hint?: string;
  to: string;
  icon: React.ElementType;
  children: React.ReactNode;
  disabled?: boolean;
  onBlocked?: () => void;
}> = ({ to, icon: Icon, children, disabled, hint, onBlocked }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const isActive =
    location.pathname === to ||
    (to !== '/' && location.pathname.startsWith(`${to}/`));

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (disabled) {
      onBlocked?.();
      return;
    }
    navigate(to);
  };

  return (
    <button
      onClick={handleClick}
      aria-current={isActive ? 'page' : undefined}
      className={clsx(
        'zh-nav-button',
        isActive && 'zh-nav-button--active'
      )}
      style={{ cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.65 : 1 }}
    >
      <Icon className="zh-nav-button__icon h-5 w-5" />
      <span className="zh-nav-button__copy">
        <span className="zh-nav-button__label">{children}</span>
        {hint ? <span className="zh-nav-button__hint">{hint}</span> : null}
      </span>
    </button>
  );
};

export const AppShell: React.FC = () => {
  const { logout, isLimitedAdmin } = useAuth();
  const { isConnected } = useWebSocket();
  const { t } = useTranslation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleBlockedNav = () => {
    toast.error(t('auth.accessDenied'));
  };

  useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  const navItems = useMemo(
    () => [
      {
        to: '/',
        icon: LayoutDashboard,
        label: t('dashboard.title'),
        hint: t('dashboard.subtitle'),
      },
      {
        to: '/devices',
        icon: Network,
        label: t('devices.title'),
        hint: 'Inventory, recognition, and probe evidence',
      },
      {
        to: '/topology',
        icon: Activity,
        label: t('topology.title'),
        hint: 'Graph view with device detail drawer',
      },
      {
        to: '/attacks',
        icon: Shield,
        label: t('attack.title'),
        hint: t('attack.subtitle'),
      },
      {
        to: '/logs',
        icon: Terminal,
        label: t('logsPage.title'),
        hint: t('logsPage.subtitle'),
      },
      {
        to: '/settings',
        icon: Settings,
        label: t('settings.title'),
        hint: t('settings.subtitle'),
      },
    ],
    [t]
  );

  const activeItem =
    navItems.find(
      (item) =>
        location.pathname === item.to ||
        (item.to !== '/' && location.pathname.startsWith(`${item.to}/`))
    ) || navItems[0];

  return (
    <div className="zh-shell">
      {isSidebarOpen && (
        <div
          className="zh-shell__overlay lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <Surface
        className="zh-shell__nav"
        data-open={isSidebarOpen}
        tone="raised"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="zh-brand">
            <div className="zh-brand__mark">
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <p className="zh-kicker">Security Console</p>
              <h1 className="zh-brand__title">ZenetHunter</h1>
              <p className="zh-brand__copy">WinUI-inspired network operations workspace</p>
            </div>
          </div>
          <Button
            aria-label="Close navigation"
            className="lg:hidden"
            onClick={() => setIsSidebarOpen(false)}
            size="icon"
            variant="ghost"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <Surface className="p-4" tone="subtle">
          <div className="zh-toolbar zh-toolbar--spread">
            <div>
              <p className="zh-kicker">Session</p>
              <p className="mt-2 text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                {isLimitedAdmin ? 'Limited access mode' : 'Full console access'}
              </p>
            </div>
            {isLimitedAdmin ? (
              <ShieldAlert className="h-5 w-5" style={{ color: 'var(--warning)' }} />
            ) : (
              <ShieldCheck className="h-5 w-5" style={{ color: 'var(--success)' }} />
            )}
          </div>
          <div className="zh-status-strip mt-4">
            <span className={clsx('zh-status-chip', isConnected && 'zh-status-chip--live')}>
              <span className="zh-status-chip__dot" />
              {isConnected ? t('settings.connected') : t('settings.disconnected')}
            </span>
            <span className="zh-status-chip">
              {isLimitedAdmin ? 'Settings only' : 'All routes available'}
            </span>
          </div>
        </Surface>

        <nav className="zh-nav-list flex-1 overflow-y-auto" aria-label="Primary">
          {navItems.map((item) => (
            <NavItem
              key={item.to}
              disabled={isLimitedAdmin && item.to !== '/settings'}
              hint={item.hint}
              icon={item.icon}
              onBlocked={handleBlockedNav}
              to={item.to}
            >
              {item.label}
            </NavItem>
          ))}
        </nav>

        <div className="zh-divider pt-4">
          <Button
            onClick={handleLogout}
            leadingIcon={<LogOut className="h-4 w-4" />}
            variant="secondary"
            fullWidth
          >
            Sign Out
          </Button>
        </div>
      </Surface>

      <div className="zh-shell__main">
        <Surface className="zh-shell__topbar" tone="raised">
          <div className="zh-toolbar__group">
            <Button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden"
              size="icon"
              variant="ghost"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="zh-shell__topbar-title">
              <p className="zh-kicker">Workspace</p>
              <h2>{activeItem.label}</h2>
            </div>
          </div>
          <div className="zh-status-strip">
            <span className={clsx('zh-status-chip', isConnected && 'zh-status-chip--live')}>
              <span className="zh-status-chip__dot" />
              {isConnected ? 'Live backend' : 'Reconnecting'}
            </span>
            {isLimitedAdmin ? <span className="zh-status-chip">Limited admin</span> : null}
          </div>
        </Surface>
        <main className="zh-shell__content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
