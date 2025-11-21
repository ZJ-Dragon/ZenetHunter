import { createBrowserRouter } from 'react-router-dom';
import { Login } from './pages/Login';
import { NotFound } from './pages/NotFound';
import { DeviceList } from './pages/DeviceList';
import { Topology } from './pages/Topology';
import { SetupWizard } from './pages/SetupWizard';
import { AppShell } from './components/layout/AppShell';
import { RequireAuth } from './components/auth/RequireAuth';
import { OOBEGuard } from './components/auth/OOBEGuard';

// Placeholder for Dashboard
const Dashboard = () => (
  <div>
    <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
    <p className="mt-2 text-gray-600">Welcome to ZenetHunter. Select an option from the sidebar.</p>
  </div>
);

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
      <RequireAuth>
        <OOBEGuard>
          <AppShell />
        </OOBEGuard>
      </RequireAuth>
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
        element: <div>Interference Page (Coming Soon)</div>,
      },
      {
        path: 'settings',
        element: <div>Settings Page (Coming Soon)</div>,
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);
