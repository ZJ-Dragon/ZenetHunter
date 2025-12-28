import { createBrowserRouter } from 'react-router-dom';
import { Login } from './pages/Login';
import { NotFound } from './pages/NotFound';
import { DeviceList } from './pages/DeviceList';
import { Topology } from './pages/Topology';
import { AttackDashboard } from './pages/AttackDashboard';
import { Logs } from './pages/Logs';
import { SetupWizard } from './pages/SetupWizard';
import { Dashboard } from './pages/Dashboard';
import { Settings } from './pages/Settings';
import { AppShell } from './components/layout/AppShell';
import { RequireAuth } from './components/auth/RequireAuth';
import { InitialRouteGuard } from './components/auth/InitialRouteGuard';

// Router Configuration
export const router = createBrowserRouter([
  {
    path: '/setup',
    element: <SetupWizard />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <InitialRouteGuard>
        <RequireAuth>
          <AppShell />
        </RequireAuth>
      </InitialRouteGuard>
    ),
    errorElement: <NotFound />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'devices',
        element: <DeviceList />,
      },
      {
        path: 'topology',
        element: <Topology />,
      },
      {
        path: 'attacks',
        element: <AttackDashboard />,
      },
      {
        path: 'logs',
        element: <Logs />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);
