import React, { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph2D, { ForceGraphMethods, NodeObject } from 'react-force-graph-2d';
import { TopologyNode, NetworkTopology } from '../../types/topology';

interface TopologyGraphProps {
  data: NetworkTopology;
  onNodeClick: (node: TopologyNode) => void;
}

export const TopologyGraph: React.FC<TopologyGraphProps> = ({ data, onNodeClick }) => {
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState<TopologyNode | null>(null);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', updateDimensions);
    updateDimensions();

    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Auto-zoom to fit when data changes
  useEffect(() => {
    if (graphRef.current && data.nodes.length > 0) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 20);
      }, 100);
    }
  }, [data]);

  // Enhanced node painting with modern meltgo style
  const nodePaint = useCallback((node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const topologyNode = node as unknown as TopologyNode & { x: number; y: number; vx?: number; vy?: number };
    const label = topologyNode.label || topologyNode.id || 'Unknown';
    const fontSize = Math.max(10, 14 / globalScale);
    const baseRadius = 8;
    const radius = baseRadius / Math.max(0.5, globalScale);
    const isHovered = hoveredNode?.id === topologyNode.id;

    // Determine node color and style
    let nodeColor = '#0078d4'; // Default blue
    let nodeBorderColor = '#005a9e';
    let nodeGlow = false;

    if (topologyNode.data?.status === 'offline') {
      nodeColor = '#6b7280'; // gray
      nodeBorderColor = '#4b5563';
    } else if (topologyNode.data?.status === 'blocked') {
      nodeColor = '#dc2626'; // red
      nodeBorderColor = '#991b1b';
      nodeGlow = true;
    } else if (topologyNode.type === 'router') {
      nodeColor = '#7c3aed'; // purple
      nodeBorderColor = '#5b21b6';
    } else if (topologyNode.data?.status === 'online') {
      nodeColor = '#10b981'; // green
      nodeBorderColor = '#059669';
    }

    // Draw glow effect for hovered or important nodes
    if (isHovered || nodeGlow) {
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

    // Draw inner highlight
    ctx.beginPath();
    ctx.arc(topologyNode.x - radius * 0.3, topologyNode.y - radius * 0.3, radius * 0.4, 0, 2 * Math.PI, false);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.fill();

    // Draw label with background for better readability
    if (globalScale > 0.5) {
      const textY = topologyNode.y + radius + fontSize + 4;
      const textWidth = ctx.measureText(label).width;
      const padding = 4;

      // Label background
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(
        topologyNode.x - textWidth / 2 - padding,
        textY - fontSize - padding,
        textWidth + padding * 2,
        fontSize + padding * 2
      );

      // Label text
      ctx.font = `${fontSize}px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, topologyNode.x, textY - fontSize);
    }

    // Reset shadow
    ctx.shadowBlur = 0;
  }, [hoveredNode]);

  // Enhanced link painting
  const linkPaint = useCallback((link: { source: TopologyNode & { x: number; y: number }; target: TopologyNode & { x: number; y: number } }, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const source = link.source as TopologyNode & { x: number; y: number };
    const target = link.target as TopologyNode & { x: number; y: number };

    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    ctx.lineTo(target.x, target.y);

    // Modern link style with gradient
    const gradient = ctx.createLinearGradient(source.x, source.y, target.x, target.y);
    gradient.addColorStop(0, 'rgba(0, 120, 212, 0.3)');
    gradient.addColorStop(1, 'rgba(0, 120, 212, 0.1)');

    ctx.strokeStyle = gradient;
    ctx.lineWidth = Math.max(1, 2 / globalScale);
    ctx.stroke();
  }, []);

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
      <ForceGraph2D
        ref={graphRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={data}
        nodeLabel="label"
        nodeCanvasObject={nodePaint}
        linkCanvasObject={linkPaint}
        onNodeClick={(node) => onNodeClick(node as unknown as TopologyNode)}
        onNodeHover={(node) => setHoveredNode(node as unknown as TopologyNode | null)}
        linkColor={() => 'rgba(0, 120, 212, 0.2)'}
        linkWidth={1.5}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={() => 'rgba(0, 120, 212, 0.4)'}
        cooldownTicks={100}
        onEngineStop={() => {
          if (graphRef.current && data.nodes.length > 0) {
            graphRef.current.zoomToFit(400, 20);
          }
        }}
        d3AlphaDecay={0.0228}
        d3VelocityDecay={0.4}
        nodeRelSize={6}
      />
    </div>
  );
};
