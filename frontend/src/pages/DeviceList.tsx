import React, { useEffect, useState, useMemo } from 'react';
import { Device, DeviceStatus, DeviceType } from '../types/device';
import { deviceService } from '../lib/services/device';
import { Search, Filter, RefreshCw, Laptop, Smartphone, Router, Shield, Wifi } from 'lucide-react';
import { clsx } from 'clsx';

const DeviceIcon = ({ type }: { type: DeviceType }) => {
  switch (type) {
    case DeviceType.ROUTER:
      return <Router className="h-5 w-5 text-purple-500" />;
    case DeviceType.PC:
      return <Laptop className="h-5 w-5 text-blue-500" />;
    case DeviceType.MOBILE:
      return <Smartphone className="h-5 w-5 text-green-500" />;
    case DeviceType.IOT:
      return <Wifi className="h-5 w-5 text-orange-500" />;
    default:
      return <Shield className="h-5 w-5 text-gray-400" />;
  }
};

const StatusBadge = ({ status }: { status: DeviceStatus }) => {
  const styles = {
    [DeviceStatus.ONLINE]: 'bg-green-100 text-green-800',
    [DeviceStatus.OFFLINE]: 'bg-gray-100 text-gray-800',
    [DeviceStatus.BLOCKED]: 'bg-red-100 text-red-800',
  };

  return (
    <span className={clsx('px-2 inline-flex text-xs leading-5 font-semibold rounded-full', styles[status])}>
      {status}
    </span>
  );
};

export const DeviceList: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<DeviceStatus | 'all'>('all');

  const fetchDevices = async () => {
    setIsLoading(true);
    try {
      const data = await deviceService.getAll();
      setDevices(data);
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const filteredDevices = useMemo(() => {
    return devices.filter((device) => {
      const matchesSearch =
        device.name?.toLowerCase().includes(search.toLowerCase()) ||
        device.ip.includes(search) ||
        device.mac.toLowerCase().includes(search.toLowerCase()) ||
        device.vendor?.toLowerCase().includes(search.toLowerCase());

      const matchesStatus = filterStatus === 'all' || device.status === filterStatus;

      return matchesSearch && matchesStatus;
    });
  }, [devices, search, filterStatus]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Network Devices</h1>
        <button
          onClick={fetchDevices}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none"
        >
          <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
            placeholder="Search by Name, IP, MAC or Vendor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="w-full sm:w-48">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Filter className="h-5 w-5 text-gray-400" />
            </div>
            <select
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500 sm:text-sm"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as DeviceStatus | 'all')}
            >
              <option value="all">All Status</option>
              <option value={DeviceStatus.ONLINE}>Online</option>
              <option value={DeviceStatus.OFFLINE}>Offline</option>
              <option value={DeviceStatus.BLOCKED}>Blocked</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MAC Address</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Seen</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredDevices.length > 0 ? (
                filteredDevices.map((device) => (
                  <tr key={device.mac} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center bg-gray-100 rounded-full">
                          <DeviceIcon type={device.type} />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{device.name || 'Unknown Device'}</div>
                          <div className="text-sm text-gray-500">{device.vendor || 'Unknown Vendor'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{device.ip}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-sm text-gray-500">
                      {device.mac}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={device.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(device.last_seen).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center text-gray-500">
                    No devices found matching your criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
