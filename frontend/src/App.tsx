import React, { useCallback, useMemo, useState } from 'react';

// --- Types (keep minimal; align later with backend DTOs) ---------------------
type View = 'home' | 'devices' | 'topology';

interface Device {
  id?: string;
  ip?: string;
  mac?: string;
  alias?: string;
  vendor?: string;
  status?: 'online' | 'offline' | 'unknown';
}

// --- Presentational bits -----------------------------------------------------
const Page: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ maxWidth: 1080, margin: '0 auto', padding: '24px' }}>
    <header style={{ marginBottom: 24 }}>
      <h1 style={{ margin: 0, fontSize: 28 }}>ZenetHunter</h1>
      <p style={{ margin: '6px 0 0', color: '#666' }}>{title}</p>
    </header>
    {children}
  </div>
);

const Card: React.FC<{
  title: string;
  description: string;
  onClick?: () => void;
}> = ({ title, description, onClick }) => (
  <button
    onClick={onClick}
    style={{
      display: 'block',
      textAlign: 'left',
      width: '100%',
      border: '1px solid #e5e7eb',
      borderRadius: 12,
      padding: '16px 18px',
      marginBottom: 16,
      background: '#fff',
      cursor: 'pointer',
      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
    }}
  >
    <div style={{ fontWeight: 600, fontSize: 16 }}>{title}</div>
    <div style={{ color: '#6b7280', marginTop: 6, fontSize: 14 }}>{description}</div>
  </button>
);

const Pill: React.FC<{ color?: string; children: React.ReactNode }> = ({ color = '#e5e7eb', children }) => (
  <span
    style={{
      padding: '2px 8px',
      borderRadius: 999,
      background: color,
      fontSize: 12,
      marginLeft: 8,
    }}
  >
    {children}
  </span>
);

// --- Utilities ---------------------------------------------------------------
const statusColor = (s: Device['status']) => {
  switch (s) {
    case 'online':
      return '#dcfce7';
    case 'offline':
      return '#fee2e2';
    default:
      return '#e5e7eb';
  }
};

// --- Main App ---------------------------------------------------------------
const App: React.FC = () => {
  const [view, setView] = useState<View>('home');
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch('/api/devices');
      if (!resp.ok) {
        throw new Error(`API responded ${resp.status}`);
      }
      const data = (await resp.json()) as Device[] | { items?: Device[] };
      const items = Array.isArray(data) ? data : data.items ?? [];
      setDevices(items);
    } catch (e: unknown) {
      setDevices([]);
      setError(
        `Failed to fetch /api/devices: ${
          e instanceof Error ? e.message : String(e)
        }. This is expected in early scaffolding — backend endpoint may not exist yet.`,
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const body = useMemo(() => {
    if (view === 'home') {
      return (
        <>
          <Card
            title="Devices"
            description="View discovered devices, try a demo fetch, and manage allow/deny lists."
            onClick={() => setView('devices')}
          />
          <Card
            title="Topology"
            description="Preview the network map (force‑directed or layered) and inspect nodes."
            onClick={() => setView('topology')}
          />
        </>
      );
    }

    if (view === 'devices') {
      return (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <button
              onClick={fetchDevices}
              disabled={loading}
              style={{
                padding: '8px 12px',
                borderRadius: 8,
                border: '1px solid #d1d5db',
                background: loading ? '#f3f4f6' : '#fff',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Loading…' : 'Fetch devices'}
            </button>
            <button
              onClick={() => setView('home')}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', background: '#fff' }}
            >
              ← Back
            </button>
          </div>

          {error && (
            <div style={{ marginBottom: 12, color: '#b91c1c' }}>
              {error}
            </div>
          )}

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  <th style={{ textAlign: 'left', padding: '10px', borderBottom: '1px solid #e5e7eb' }}>IP</th>
                  <th style={{ textAlign: 'left', padding: '10px', borderBottom: '1px solid #e5e7eb' }}>MAC</th>
                  <th style={{ textAlign: 'left', padding: '10px', borderBottom: '1px solid #e5e7eb' }}>Alias</th>
                  <th style={{ textAlign: 'left', padding: '10px', borderBottom: '1px solid #e5e7eb' }}>Vendor</th>
                  <th style={{ textAlign: 'left', padding: '10px', borderBottom: '1px solid #e5e7eb' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {devices.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: '16px', color: '#6b7280' }}>
                      No data yet. Click <strong>Fetch devices</strong> to try the backend endpoint, or hook up the scanner later.
                    </td>
                  </tr>
                ) : (
                  devices.map((d, i) => (
                    <tr key={d.id ?? `${d.mac ?? 'unknown'}-${i}`}>
                      <td style={{ padding: '10px', borderBottom: '1px solid #f3f4f6' }}>{d.ip ?? '—'}</td>
                      <td style={{ padding: '10px', borderBottom: '1px solid #f3f4f6' }}>{d.mac ?? '—'}</td>
                      <td style={{ padding: '10px', borderBottom: '1px solid #f3f4f6' }}>{d.alias ?? '—'}</td>
                      <td style={{ padding: '10px', borderBottom: '1px solid #f3f4f6' }}>{d.vendor ?? '—'}</td>
                      <td style={{ padding: '10px', borderBottom: '1px solid #f3f4f6' }}>
                        <span>
                          {d.status ?? 'unknown'}
                          <Pill color={statusColor(d.status)}>{d.status ?? 'unknown'}</Pill>
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    // view === 'topology'
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <button
            onClick={() => setView('home')}
            style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', background: '#fff' }}
          >
            ← Back
          </button>
        </div>
        <div
          style={{
            height: 420,
            border: '1px dashed #cbd5e1',
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b',
          }}
        >
          Topology preview placeholder — plug in your graph component later.
        </div>
      </div>
    );
  }, [view, devices, loading, error, fetchDevices]);

  return <Page title={view === 'home' ? 'Choose a module to begin' : view === 'devices' ? 'Devices' : 'Topology'}>{body}</Page>;
};

export default App;
