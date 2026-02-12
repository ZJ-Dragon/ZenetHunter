import React, { useEffect, useState, useCallback } from 'react';
import { TopologyGraph } from '../components/topology/TopologyGraph';
import { NodeDrawer } from '../components/topology/NodeDrawer';
import { topologyService } from '../lib/services/topology';
import { NetworkTopology, TopologyNode } from '../types/topology';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { WSEventType } from '../types/websocket';
import { RefreshCw, Network, Terminal } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ScanButton } from '../components/actions/ScanButton';
import { RealtimeLogPanel } from '../components/logs/RealtimeLogPanel';
import { clsx } from 'clsx';

export const Topology: React.FC = () => {
  const [data, setData] = useState<NetworkTopology>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const { t } = useTranslation();

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
          <Network className="h-6 w-6" style={{ color: 'var(--winui-accent)' }} />
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--winui-text-primary)', letterSpacing: '-0.02em' }}>
            {t('topology.title')}
          </h1>
        </div>
        <div className="flex space-x-2">
          <ScanButton />
          <button
            onClick={() => setShowLogs(!showLogs)}
            className={clsx(
              "btn-winui-secondary inline-flex items-center",
              showLogs && "bg-opacity-80"
            )}
          >
            <Terminal className="h-4 w-4 mr-2" />
            {t('topology.logs')}
          </button>
          <button
            onClick={() => {
              setIsLoading(true);
              fetchTopology();
            }}
            className="btn-winui-secondary inline-flex items-center"
          >
            <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            {t('topology.refresh')}
          </button>
        </div>
      </div>

      <div className="flex-1 relative card-winui overflow-hidden" style={{ borderRadius: 'var(--winui-radius-lg)' }}>
        {isLoading && data.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center z-10" style={{ backgroundColor: 'var(--winui-surface)', opacity: 0.9 }}>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2" style={{ borderColor: 'var(--winui-accent)' }}></div>
          </div>
        )}

        {!isLoading && data.nodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center z-10" style={{ backgroundColor: 'var(--winui-surface)' }}>
            <Network className="h-16 w-16 mb-4" style={{ color: 'var(--winui-text-tertiary)' }} />
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--winui-text-primary)' }}>
              {t('topology.emptyTitle')}
            </h3>
            <p className="mb-6" style={{ color: 'var(--winui-text-secondary)' }}>
              {t('topology.emptyHint')}
            </p>
            <ScanButton />
          </div>
        )}

        <TopologyGraph
          data={data}
          onNodeClick={setSelectedNode}
        />

        {/* Drawer Overlay */}
        {selectedNode && (
          <div
            className="absolute inset-0 z-40 transition-opacity"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.4)', backdropFilter: 'blur(4px)' }}
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

      {/* Realtime Log Panel */}
      <RealtimeLogPanel
        isOpen={showLogs}
        onClose={() => setShowLogs(false)}
        maxLogs={50}
      />
    </div>
  );
};
