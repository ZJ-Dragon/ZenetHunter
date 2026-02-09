import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { ZoomIn, ZoomOut, Focus, Maximize2 } from 'lucide-react';
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d';
import { forceCollide, forceManyBody } from 'd3-force-3d';
import { TopologyNode, NetworkTopology } from '../../types/topology';

interface TopologyGraphProps {
  data: NetworkTopology;
  onNodeClick: (node: TopologyNode) => void;
}

export const TopologyGraph: React.FC<TopologyGraphProps> = ({ data, onNodeClick }) => {
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [hoveredNode, setHoveredNode] = useState<TopologyNode | null>(null);
  const [graphReady, setGraphReady] = useState(false);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const lastClickRef = useRef<number>(0);
   const [isInitializing, setIsInitializing] = useState(true);

  const preparedData = useMemo(() => {
    const nodes = data.nodes.map((n, idx) => {
      const device = n.data;
      const displayName =
        device.display_name ||
        device.name ||
        device.alias ||
        device.model ||
        device.model_guess ||
        String(device.ip);
      const displayVendor =
        device.display_vendor ||
        device.vendor ||
        device.vendor_guess ||
        'Unknown';
      const node: any = {
        ...n,
        primaryLabel: displayName,
        vendorLabel: displayVendor,
      };

      // Anchor router/gateway near center
      if (n.type === 'router' || n.type === 'gateway') {
        node.fx = 0;
        node.fy = 0;
      } else {
        const angle = (idx / Math.max(1, data.nodes.length)) * Math.PI * 2;
        const radius = 280 + idx * 6;
        node.x = Math.cos(angle) * radius;
        node.y = Math.sin(angle) * radius;
      }
      return node;
    });

    const links = data.links.map((l) => ({ ...l }));
    return { nodes, links };
  }, [data]);

  useEffect(() => {
    if (!containerRef.current) return;

    const updateDimensions = () => {
      if (!containerRef.current) return;
      const { clientWidth, clientHeight } = containerRef.current;
      setDimensions({
        width: clientWidth,
        height: clientHeight,
      });
    };

    const observer = new ResizeObserver(() => {
      updateDimensions();
    });

    observer.observe(containerRef.current);
    updateDimensions();

    return () => observer.disconnect();
  }, []);

  const refreshGraphLayout = useCallback(() => {
    if (!graphRef.current || data.nodes.length === 0) return;
    requestAnimationFrame(() => {
      graphRef.current?.zoomToFit(400, 32);
    });
  }, [data.nodes.length]);

  // Mark graph ready when both data and dimensions are present
  useEffect(() => {
    const ready = dimensions.width > 0 && dimensions.height > 0;
    setGraphReady(ready);
    setIsInitializing(!ready || (ready && data.nodes.length > 0));
    if (ready && data.nodes.length > 0) {
      refreshGraphLayout();
    }
  }, [data.nodes.length, dimensions.width, dimensions.height, refreshGraphLayout]);

  useEffect(() => {
    if (!graphReady || !graphRef.current) return;
    graphRef.current.d3Force('collide', forceCollide(38));
    graphRef.current.d3Force('charge', forceManyBody().strength(-260));
    refreshGraphLayout();
  }, [graphReady, refreshGraphLayout]);

  useEffect(() => {
    if (!graphReady) return;
    // Extra nudge after data changes
    const id = setTimeout(() => {
      refreshGraphLayout();
      setIsInitializing(false);
    }, 120);
    return () => clearTimeout(id);
  }, [preparedData.nodes.length, graphReady, refreshGraphLayout]);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === 'visible') {
        refreshGraphLayout();
      }
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, [refreshGraphLayout]);

  const centerOnNode = useCallback((node: any) => {
    if (!graphRef.current || !node) return;
    const { x = 0, y = 0 } = node;
    graphRef.current.centerAt(x, y, 400);
    graphRef.current.zoom(1.4, 400);
  }, []);

  const handleNodeClick = useCallback(
    (nodeObj: NodeObject) => {
      const now = Date.now();
      const topologyNode = nodeObj as unknown as TopologyNode;
      setFocusedNodeId(String(topologyNode.id));
      onNodeClick(topologyNode);

      if (now - lastClickRef.current < 300) {
        centerOnNode(nodeObj);
      }
      lastClickRef.current = now;
    },
    [centerOnNode, onNodeClick]
  );

  // Enhanced node painting with modern meltgo style
  const nodePaint = useCallback((node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const topologyNode = node as any as TopologyNode & {
      x: number;
      y: number;
      vx?: number;
      vy?: number;
      primaryLabel?: string;
      vendorLabel?: string;
    };
    const rawLabel = topologyNode.primaryLabel || topologyNode.label || topologyNode.id || 'Unknown';
    const label =
      rawLabel.length > 16 ? `${rawLabel.slice(0, 14)}…` : rawLabel;
    const vendorLabel = topologyNode.vendorLabel;
    const fontSize = Math.max(9, 14 / globalScale);
    const baseRadius = 16;
    const radius = Math.max(11, baseRadius / Math.max(0.65, globalScale));
    const isHovered = hoveredNode?.id === topologyNode.id;
    const isFocused = focusedNodeId === topologyNode.id;

    // Determine node color and style
    let nodeColor = '#0078d4'; // Default blue
    let nodeBorderColor = '#005a9e';
    let statusDot = '#0078d4';

    if (topologyNode.data?.status === 'offline') {
      nodeColor = '#6b7280'; // gray
      nodeBorderColor = '#4b5563';
      statusDot = '#9ca3af';
    } else if (topologyNode.data?.status === 'blocked') {
      nodeColor = '#dc2626'; // red
      nodeBorderColor = '#991b1b';
      statusDot = '#fca5a5';
    } else if (topologyNode.type === 'router') {
      nodeColor = '#7c3aed'; // purple
      nodeBorderColor = '#5b21b6';
      statusDot = '#a855f7';
    } else if (topologyNode.data?.status === 'online') {
      nodeColor = '#10b981'; // green
      nodeBorderColor = '#059669';
      statusDot = '#34d399';
    }

    // Draw glow effect for hovered or important nodes
    if (isHovered || isFocused) {
      ctx.shadowBlur = 15;
      ctx.shadowColor = nodeColor;
    } else {
      ctx.shadowBlur = 0;
    }

    // Draw outer ring (border)
    ctx.beginPath();
    ctx.arc(topologyNode.x, topologyNode.y, radius + 2, 0, 2 * Math.PI, false);
    ctx.fillStyle = nodeBorderColor;
    ctx.fill();

    // Draw main node circle with gradient
    const gradient = ctx.createRadialGradient(
      topologyNode.x - radius * 0.3,
      topologyNode.y - radius * 0.3,
      0,
      topologyNode.x,
      topologyNode.y,
      radius
    );
    gradient.addColorStop(0, nodeColor);
    gradient.addColorStop(1, nodeBorderColor);

    ctx.beginPath();
    ctx.arc(topologyNode.x, topologyNode.y, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Status dot
    ctx.beginPath();
    ctx.arc(topologyNode.x + radius * 0.7, topologyNode.y - radius * 0.7, radius * 0.35, 0, 2 * Math.PI, false);
    ctx.fillStyle = statusDot;
    ctx.fill();

    const showPrimaryLabel = globalScale >= 0.58 || topologyNode.type === 'router';
    const showBadges = globalScale >= 1.2;

    if (showPrimaryLabel) {
      const textY = topologyNode.y + radius + fontSize + 4;
      const textWidth = ctx.measureText(label).width;
      const padding = 6;

      // Label background
      ctx.fillStyle = 'rgba(24, 26, 27, 0.82)';
      ctx.fillRect(
        topologyNode.x - textWidth / 2 - padding,
        textY - fontSize - padding,
        textWidth + padding * 2,
        fontSize + padding * 2
      );

      // Label text
      ctx.font = `${fontSize}px 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, topologyNode.x, textY - fontSize);

      if (showBadges && vendorLabel) {
        const badge = vendorLabel.length > 16 ? `${vendorLabel.slice(0, 14)}…` : vendorLabel;
        const badgeWidth = ctx.measureText(badge).width;
        const badgeY = textY + fontSize + padding * 0.5;
        const badgePadX = 8;
        const badgePadY = 4;

        const bw = badgeWidth + badgePadX * 2;
        const bh = fontSize + badgePadY * 2;
        const bx = topologyNode.x - bw / 2;
        const by = badgeY - fontSize;
        const radius = 6;
        ctx.fillStyle = 'rgba(0, 120, 212, 0.2)';
        ctx.strokeStyle = 'rgba(0, 120, 212, 0.4)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(bx + radius, by);
        ctx.lineTo(bx + bw - radius, by);
        ctx.quadraticCurveTo(bx + bw, by, bx + bw, by + radius);
        ctx.lineTo(bx + bw, by + bh - radius);
        ctx.quadraticCurveTo(bx + bw, by + bh, bx + bw - radius, by + bh);
        ctx.lineTo(bx + radius, by + bh);
        ctx.quadraticCurveTo(bx, by + bh, bx, by + bh - radius);
        ctx.lineTo(bx, by + radius);
        ctx.quadraticCurveTo(bx, by, bx + radius, by);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#0f4c81';
        ctx.fillText(badge, topologyNode.x, by + badgePadY);
      }
    }

    // Reset shadow
    ctx.shadowBlur = 0;
  }, [hoveredNode, focusedNodeId]);

  // Enhanced link painting
  const linkPaint = useCallback((link: { source: TopologyNode & { x: number; y: number }; target: TopologyNode & { x: number; y: number } }, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const source = link.source as TopologyNode & { x: number; y: number };
    const target = link.target as TopologyNode & { x: number; y: number };
    const isHighlighted =
      hoveredNode?.id === source.id ||
      hoveredNode?.id === target.id ||
      focusedNodeId === source.id ||
      focusedNodeId === target.id;

    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    ctx.lineTo(target.x, target.y);

    // Modern link style with gradient
    const gradient = ctx.createLinearGradient(source.x, source.y, target.x, target.y);
    gradient.addColorStop(0, isHighlighted ? 'rgba(0, 120, 212, 0.55)' : 'rgba(0, 120, 212, 0.25)');
    gradient.addColorStop(1, isHighlighted ? 'rgba(0, 120, 212, 0.35)' : 'rgba(0, 120, 212, 0.1)');

    ctx.strokeStyle = gradient;
    ctx.lineWidth = Math.max(1, (isHighlighted ? 2.4 : 1.4) / globalScale);
    ctx.stroke();
  }, [focusedNodeId, hoveredNode]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full min-h-[600px] overflow-hidden"
      style={{
        backgroundColor: 'var(--winui-surface)',
        borderRadius: 'var(--winui-radius-lg)',
        position: 'relative',
      }}
    >
      {graphReady && (
        <ForceGraph2D
          key={`graph-${preparedData.nodes.length}-${preparedData.links.length}`}
          ref={graphRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={preparedData}
          nodeLabel={(node: any) => {
            const primary = node.primaryLabel || node.label;
            const ip = node.data?.ip ? `IP: ${node.data.ip}` : '';
            const vendor = node.vendorLabel ? `Vendor: ${node.vendorLabel}` : '';
            return [primary, ip, vendor].filter(Boolean).join('\n');
          }}
          nodeCanvasObject={nodePaint}
          linkCanvasObject={linkPaint}
          onNodeClick={handleNodeClick}
          onNodeHover={(node) => setHoveredNode(node as unknown as TopologyNode | null)}
          linkColor={(link: LinkObject) => {
            const sourceId = (link.source as any)?.id || link.source;
            const targetId = (link.target as any)?.id || link.target;
            const isHighlight =
              hoveredNode?.id === sourceId ||
              hoveredNode?.id === targetId ||
              focusedNodeId === sourceId ||
              focusedNodeId === targetId;
            return isHighlight ? 'rgba(0, 120, 212, 0.5)' : 'rgba(0, 120, 212, 0.15)';
          }}
          linkWidth={(link: LinkObject) => {
            const sourceId = (link.source as any)?.id || link.source;
            const targetId = (link.target as any)?.id || link.target;
            const isHighlight =
              hoveredNode?.id === sourceId ||
              hoveredNode?.id === targetId ||
              focusedNodeId === sourceId ||
              focusedNodeId === targetId;
            return isHighlight ? 2.2 : 1.2;
          }}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkDirectionalArrowColor={() => 'rgba(0, 120, 212, 0.25)'}
          cooldownTicks={120}
          onEngineStop={() => {
            refreshGraphLayout();
          }}
          d3AlphaDecay={0.022}
          d3VelocityDecay={0.35}
          nodeRelSize={6}
          enablePanInteraction
          enableZoomInteraction
        />
      )}
      {(!graphReady || isInitializing) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-sm z-10"
          style={{ color: 'var(--winui-text-secondary)', backgroundColor: 'rgba(255,255,255,0.72)' }}>
          <div className="h-10 w-10 border-2 border-t-transparent rounded-full animate-spin mb-2"
            style={{ borderColor: 'var(--winui-accent)' }} />
          Preparing layout...
        </div>
      )}
      <div className="absolute top-4 right-4 flex gap-2 z-10">
        <button
          onClick={() => {
            graphRef.current?.zoom((graphRef.current?.zoom() || 1) * 1.2, 200);
          }}
          className="btn-winui-secondary flex items-center gap-1"
        >
          <ZoomIn className="h-4 w-4" />
          Zoom In
        </button>
        <button
          onClick={() => {
            graphRef.current?.zoom((graphRef.current?.zoom() || 1) * 0.8, 200);
          }}
          className="btn-winui-secondary flex items-center gap-1"
        >
          <ZoomOut className="h-4 w-4" />
          Zoom Out
        </button>
        <button
          onClick={() => refreshGraphLayout()}
          className="btn-winui-secondary flex items-center gap-1"
        >
          <Maximize2 className="h-4 w-4" />
          Fit
        </button>
        <button
          onClick={() => {
            if (!focusedNodeId) return;
            const node = preparedData.nodes.find((n) => String(n.id) === focusedNodeId);
            centerOnNode(node as any);
          }}
          className="btn-winui-secondary flex items-center gap-1"
          disabled={!focusedNodeId}
        >
          <Focus className="h-4 w-4" />
          Focus node
        </button>
      </div>
    </div>
  );
};
