import React, { useState } from 'react';
import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom';
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
  Terminal
} from 'lucide-react';
import { clsx } from 'clsx';

const NavItem: React.FC<{ to: string; icon: React.ElementType; children: React.ReactNode }> = ({ to, icon: Icon, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={clsx(
        'flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200',
        isActive
          ? 'text-white'
          : 'hover:bg-gray-100 dark:hover:bg-gray-800'
      )}
      style={{
        backgroundColor: isActive ? 'var(--winui-accent)' : 'transparent',
        color: isActive ? '#ffffff' : 'var(--winui-text-secondary)',
      }}
    >
      <Icon 
        className="mr-3 h-5 w-5" 
        style={{ color: isActive ? '#ffffff' : 'var(--winui-text-tertiary)' }}
      />
      {children}
    </Link>
  );
};

export const AppShell: React.FC = () => {
  const { logout } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--winui-bg-primary)' }}>
      {/* Mobile Sidebar Backdrop */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-20 lg:hidden"
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.4)', backdropFilter: 'blur(4px)' }}
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar - WinUI3 Style */}
      <div className={clsx(
        'fixed inset-y-0 left-0 z-30 w-64 transform transition-transform duration-200 ease-out lg:translate-x-0 lg:static lg:inset-auto',
        'card-winui lg:shadow-none lg:border-r lg:rounded-none',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex items-center justify-between h-16 px-6" style={{ backgroundColor: 'var(--winui-accent)', color: '#ffffff' }}>
          <div className="flex items-center space-x-2">
            <Activity className="h-6 w-6" />
            <span className="text-lg font-semibold">ZenetHunter</span>
          </div>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="lg:hidden p-1 rounded-lg hover:bg-white/20 focus:outline-none transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <NavItem to="/" icon={LayoutDashboard}>Dashboard</NavItem>
          <NavItem to="/devices" icon={Network}>Devices</NavItem>
          <NavItem to="/topology" icon={Activity}>Topology</NavItem>
          <NavItem to="/attacks" icon={Shield}>Interference</NavItem>
          <NavItem to="/logs" icon={Terminal}>Logs</NavItem>
          <NavItem to="/settings" icon={Settings}>Settings</NavItem>
        </nav>

        <div className="p-4 border-t" style={{ borderColor: 'var(--winui-border-subtle)' }}>
          <button
            onClick={handleLogout}
            className="flex items-center w-full px-4 py-2 text-sm font-medium rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            style={{ color: 'var(--winui-text-secondary)' }}
          >
            <LogOut className="mr-3 h-5 w-5" style={{ color: 'var(--winui-text-tertiary)' }} />
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="lg:hidden" style={{ backgroundColor: 'var(--winui-surface)', borderBottom: '1px solid var(--winui-border-subtle)' }}>
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none transition-colors"
              style={{ color: 'var(--winui-text-secondary)' }}
            >
              <Menu className="h-6 w-6" />
            </button>
            <span className="text-lg font-semibold" style={{ color: 'var(--winui-text-primary)' }}>ZenetHunter</span>
            <div className="w-6" />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
