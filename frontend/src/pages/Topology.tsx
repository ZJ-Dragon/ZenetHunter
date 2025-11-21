import React, { useEffect, useState, useCallback } from 'react';
import { TopologyGraph } from '../components/topology/TopologyGraph';
import { NodeDrawer } from '../components/topology/NodeDrawer';
import { topologyService } from '../lib/services/topology';
import { NetworkTopology, TopologyNode } from '../types/topology';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { WSEventType } from '../types/websocket';
import { RefreshCw, Network } from 'lucide-react';
import { clsx } from 'clsx';

export const Topology: React.FC = () => {
  const [data, setData] = useState<NetworkTopology>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);

  const fetchTopology = useCallback(async () => {
    try {
      const topology = await topologyService.getTopology();
      setData(topology);
    } catch (error) {
      console.error('Failed to fetch topology:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopology();
  }, [fetchTopology]);

  // WebSocket Updates
  // When a device is added or status changes, we refresh the topology
  // In a more optimized version, we would update the local graph data directly
  // but fetching fresh topology is safer for consistency for now.
  useWebSocketEvent(WSEventType.DEVICE_ADDED, () => {
    console.log('WS: Device Added, refreshing topology');
    fetchTopology();
  });

  useWebSocketEvent(WSEventType.DEVICE_STATUS_CHANGED, () => {
    console.log('WS: Status Changed, refreshing topology');
    fetchTopology();
  });

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col relative">
      <div className="flex justify-between items-center mb-4 px-1">
        <div className="flex items-center space-x-2">
          <Network className="h-6 w-6 text-brand-600" />
          <h1 className="text-2xl font-bold text-gray-900">Network Map</h1>
        </div>
        <button
          onClick={() => {
            setIsLoading(true);
            fetchTopology();
          }}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none"
        >
          <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
          Refresh
        </button>
      </div>

      <div className="flex-1 relative bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        {isLoading && data.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center z-10 bg-white bg-opacity-80">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-600"></div>
          </div>
        )}
        
        <TopologyGraph 
          data={data} 
          onNodeClick={setSelectedNode} 
        />

        {/* Drawer Overlay */}
        {selectedNode && (
          <div 
            className="absolute inset-0 bg-black bg-opacity-25 z-40 transition-opacity"
            onClick={() => setSelectedNode(null)}
          />
        )}

        {/* Drawer */}
        {selectedNode && (
          <NodeDrawer 
            node={selectedNode} 
            onClose={() => setSelectedNode(null)} 
          />
        )}
      </div>
    </div>
  );
};

