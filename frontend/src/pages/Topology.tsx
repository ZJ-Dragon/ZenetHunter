import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Network,
  RefreshCw,
  Terminal,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ScanButton } from '../components/actions/ScanButton';
import { RealtimeLogPanel } from '../components/logs/RealtimeLogPanel';
import { NodeDrawer } from '../components/topology/NodeDrawer';
import { TopologyGraph } from '../components/topology/TopologyGraph';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { Surface } from '../components/ui/Surface';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { topologyService } from '../lib/services/topology';
import { Device } from '../types/device';
import { NetworkTopology, TopologyNode } from '../types/topology';
import { WSEventType } from '../types/websocket';

export const Topology: React.FC = () => {
  const [data, setData] = useState<NetworkTopology>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const { t } = useTranslation();

  const fetchTopology = useCallback(async () => {
    setIsLoading(true);
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

  useWebSocketEvent(WSEventType.DEVICE_ADDED, fetchTopology);
  useWebSocketEvent(WSEventType.DEVICE_STATUS_CHANGED, fetchTopology);
  useWebSocketEvent(WSEventType.DEVICE_UPDATED, fetchTopology);
  useWebSocketEvent(WSEventType.DEVICE_RECOGNITION_UPDATED, fetchTopology);
  useWebSocketEvent(WSEventType.RECOGNITION_OVERRIDDEN, fetchTopology);
  useWebSocketEvent(WSEventType.DEVICE_LIST_CLEARED, fetchTopology);

  const onlineCount = useMemo(
    () => data.nodes.filter((node) => node.data?.status === 'online').length,
    [data.nodes]
  );

  const blockedCount = useMemo(
    () => data.nodes.filter((node) => node.data?.status === 'blocked').length,
    [data.nodes]
  );

  const handleDeviceUpdate = (device: Device) => {
    setData((previous) => ({
      ...previous,
      nodes: previous.nodes.map((node) =>
        node.data.mac === device.mac
          ? {
              ...node,
              label:
                device.display_name ||
                device.name ||
                device.alias ||
                device.model ||
                device.mac,
              data: device,
            }
          : node
      ),
    }));

    setSelectedNode((previous) =>
      previous && previous.data.mac === device.mac
        ? {
            ...previous,
            label:
              device.display_name ||
              device.name ||
              device.alias ||
              device.model ||
              device.mac,
            data: device,
          }
        : previous
    );
  };

  return (
    <div className="zh-page">
      <PageHeader
        actions={
          <>
            <ScanButton />
            <Button
              leadingIcon={<Terminal className="h-4 w-4" />}
              onClick={() => setShowLogs((previous) => !previous)}
              variant={showLogs ? 'accent' : 'secondary'}
            >
              {t('topology.logs')}
            </Button>
            <Button
              leadingIcon={<RefreshCw className={isLoading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />}
              onClick={fetchTopology}
              variant="secondary"
            >
              {t('topology.refresh')}
            </Button>
          </>
        }
        eyebrow={t('topology.eyebrow')}
        icon={Network}
        subtitle={t('topology.subtitle')}
        title={t('topology.title')}
      />

      <div className="zh-stat-grid">
        <StatCard
          hint={t('topology.nodesHint')}
          icon={Network}
          label={t('topology.nodesLabel')}
          value={data.nodes.length}
        />
        <StatCard
          hint={t('topology.linksHint')}
          icon={Activity}
          label={t('topology.linksLabel')}
          tone="var(--accent)"
          value={data.links.length}
        />
        <StatCard
          hint={t('topology.onlineHint')}
          icon={Activity}
          label={t('devices.statusOnline')}
          tone="var(--success)"
          value={onlineCount}
        />
        <StatCard
          hint={t('topology.blockedHint')}
          icon={Activity}
          label={t('devices.statusBlocked')}
          tone="var(--danger)"
          value={blockedCount}
        />
      </div>

      <Surface className="p-5 lg:p-6" tone="raised">
        <div className="zh-toolbar zh-toolbar--spread">
          <div>
            <p className="zh-kicker">{t('topology.canvasKicker')}</p>
            <h2 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
              {t('topology.canvasTitle')}
            </h2>
          </div>
          <div className="zh-legend">
            <div className="zh-legend__item">
              <span className="zh-legend__swatch" style={{ background: '#7c4dff' }} />
              {t('topology.legendRouter')}
            </div>
            <div className="zh-legend__item">
              <span className="zh-legend__swatch" style={{ background: 'var(--success)' }} />
              {t('topology.legendOnline')}
            </div>
            <div className="zh-legend__item">
              <span className="zh-legend__swatch" style={{ background: 'var(--danger)' }} />
              {t('topology.legendBlocked')}
            </div>
            <div className="zh-legend__item">
              <span className="zh-legend__swatch" style={{ background: 'var(--text-tertiary)' }} />
              {t('topology.legendOffline')}
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-[1.5rem] border" style={{ borderColor: 'var(--border)' }}>
          {isLoading && data.nodes.length === 0 ? (
            <div className="grid min-h-[42rem] place-items-center">
              <RefreshCw className="h-10 w-10 animate-spin" style={{ color: 'var(--accent)' }} />
            </div>
          ) : !isLoading && data.nodes.length === 0 ? (
            <EmptyState
              action={<ScanButton />}
              description={t('topology.emptyHint')}
              icon={Network}
              title={t('topology.emptyTitle')}
            />
          ) : (
            <TopologyGraph data={data} onNodeClick={setSelectedNode} />
          )}
        </div>
      </Surface>

      {selectedNode ? (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setSelectedNode(null)}
          style={{ background: 'rgba(15, 23, 42, 0.42)', backdropFilter: 'blur(10px)' }}
        />
      ) : null}

      {selectedNode ? (
        <NodeDrawer
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          onDeviceUpdate={handleDeviceUpdate}
        />
      ) : null}

      <RealtimeLogPanel isOpen={showLogs} maxLogs={50} onClose={() => setShowLogs(false)} />
    </div>
  );
};
