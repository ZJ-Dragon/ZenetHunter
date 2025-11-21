import React from 'react';
import { X, Monitor, Smartphone, Router, Shield, Activity, Clock, Hash } from 'lucide-react';
import { TopologyNode } from '../../types/topology';
import { DeviceStatus } from '../../types/device';
import { clsx } from 'clsx';

interface NodeDrawerProps {
  node: TopologyNode | null;
  onClose: () => void;
}

export const NodeDrawer: React.FC<NodeDrawerProps> = ({ node, onClose }) => {
  if (!node) return null;

  const { data: device } = node;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <h2 className="text-lg font-medium text-gray-900">Device Details</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-500 focus:outline-none"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Identity Card */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-start space-x-4">
          <div className="flex-shrink-0">
            {device.type === 'router' ? (
              <Router className="h-10 w-10 text-purple-500" />
            ) : device.type === 'mobile' ? (
              <Smartphone className="h-10 w-10 text-green-500" />
            ) : (
              <Monitor className="h-10 w-10 text-blue-500" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">{device.name || 'Unknown Device'}</h3>
            <p className="text-sm text-gray-500">{device.vendor || 'Unknown Vendor'}</p>
            <div className={clsx(
              "mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
              device.status === DeviceStatus.ONLINE ? "bg-green-100 text-green-800" :
              device.status === DeviceStatus.BLOCKED ? "bg-red-100 text-red-800" :
              "bg-gray-100 text-gray-800"
            )}>
              {device.status.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Network Info */}
        <div>
          <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Network Information</h4>
          <dl className="grid grid-cols-1 gap-4">
            <div className="flex items-center">
              <Activity className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <dt className="text-xs text-gray-500">IP Address</dt>
                <dd className="text-sm font-medium text-gray-900">{device.ip}</dd>
              </div>
            </div>
            <div className="flex items-center">
              <Hash className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <dt className="text-xs text-gray-500">MAC Address</dt>
                <dd className="text-sm font-medium text-gray-900 font-mono">{device.mac}</dd>
              </div>
            </div>
          </dl>
        </div>

        {/* Activity Info */}
        <div>
          <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Activity</h4>
          <dl className="grid grid-cols-1 gap-4">
            <div className="flex items-center">
              <Clock className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <dt className="text-xs text-gray-500">Last Seen</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {new Date(device.last_seen).toLocaleString()}
                </dd>
              </div>
            </div>
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <dt className="text-xs text-gray-500">Attack Status</dt>
                <dd className="text-sm font-medium text-gray-900">{device.attack_status}</dd>
              </div>
            </div>
          </dl>
        </div>
      </div>

      {/* Actions */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <button
          className="w-full flex justify-center items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
        >
          <Shield className="mr-2 h-4 w-4" />
          Block Device
        </button>
      </div>
    </div>
  );
};
