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
  Activity
} from 'lucide-react';
import { clsx } from 'clsx';

const NavItem: React.FC<{ to: string; icon: React.ElementType; children: React.ReactNode }> = ({ to, icon: Icon, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={clsx(
        'flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors',
        isActive
          ? 'bg-brand-50 text-brand-700'
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
      )}
    >
      <Icon className={clsx('mr-3 h-5 w-5', isActive ? 'text-brand-500' : 'text-gray-400')} />
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
    <div className="min-h-screen bg-gray-100 flex">
      {/* Mobile Sidebar Backdrop */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 z-20 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={clsx(
        'fixed inset-y-0 left-0 z-30 w-64 bg-white shadow-lg transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-auto',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex items-center justify-between h-16 px-6 bg-brand-600 text-white">
          <div className="flex items-center space-x-2">
            <Activity className="h-6 w-6" />
            <span className="text-lg font-bold">ZenetHunter</span>
          </div>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="lg:hidden p-1 rounded-md hover:bg-brand-700 focus:outline-none"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          <NavItem to="/" icon={LayoutDashboard}>Dashboard</NavItem>
          <NavItem to="/devices" icon={Network}>Devices</NavItem>
          <NavItem to="/attacks" icon={Shield}>Interference</NavItem>
          <NavItem to="/settings" icon={Settings}>Settings</NavItem>
        </nav>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="flex items-center w-full px-4 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
          >
            <LogOut className="mr-3 h-5 w-5 text-gray-400" />
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white shadow-sm lg:hidden">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-brand-500 lg:hidden"
            >
              <Menu className="h-6 w-6" />
            </button>
            <span className="text-lg font-medium text-gray-900">ZenetHunter</span>
            <div className="w-6" /> {/* Spacer for centering if needed */}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
