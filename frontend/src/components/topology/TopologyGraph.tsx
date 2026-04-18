import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ForceGraph2D, {
  ForceGraphMethods,
  NodeObject,
} from 'react-force-graph-2d';
import { NetworkTopology, TopologyNode } from '../../types/topology';

interface TopologyGraphProps {
  data: NetworkTopology;
  onNodeClick: (node: TopologyNode) => void;
}

const readPalette = () => {
  const styles = getComputedStyle(document.documentElement);
  return {
    accent: styles.getPropertyValue('--accent').trim() || '#0a64d8',
    border: styles.getPropertyValue('--border').trim() || 'rgba(15, 23, 42, 0.08)',
    danger: styles.getPropertyValue('--danger').trim() || '#c42b1c',
    success: styles.getPropertyValue('--success').trim() || '#0f7b0f',
    surface: styles.getPropertyValue('--surface-raised').trim() || '#ffffff',
    tertiary: styles.getPropertyValue('--text-tertiary').trim() || '#6f8197',
    text: styles.getPropertyValue('--text-primary').trim() || '#111827',
    warning: styles.getPropertyValue('--warning').trim() || '#b46900',
  };
};

export const TopologyGraph: React.FC<TopologyGraphProps> = ({
  data,
  onNodeClick,
}) => {
  const { t } = useTranslation();
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState<TopologyNode | null>(null);

  useEffect(() => {
    const updateDimensions = () => {
      if (!containerRef.current) {
        return;
      }

      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
      });
    };

    window.addEventListener('resize', updateDimensions);
    updateDimensions();

    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (graphRef.current && data.nodes.length > 0) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 40);
      }, 120);
    }
  }, [data]);

  const nodePaint = useCallback(
    (node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const palette = readPalette();
      const topologyNode = node as unknown as TopologyNode & {
        x: number;
        y: number;
      };
      const label = topologyNode.label || topologyNode.id || t('topology.unknownNode');
      const radius = 10 / Math.max(0.65, globalScale);
      const fontSize = Math.max(10, 13 / globalScale);
      const hovered = hoveredNode?.id === topologyNode.id;

      let fill = palette.accent;
      if (topologyNode.type === 'router') {
        fill = '#7c4dff';
      } else if (topologyNode.data?.status === 'online') {
        fill = palette.success;
      } else if (topologyNode.data?.status === 'blocked') {
        fill = palette.danger;
      } else if (topologyNode.data?.status === 'offline') {
        fill = palette.tertiary;
      }

      ctx.shadowBlur = hovered ? 18 : 0;
      ctx.shadowColor = fill;

      ctx.beginPath();
      ctx.arc(topologyNode.x, topologyNode.y, radius + 4, 0, 2 * Math.PI, false);
      ctx.fillStyle = 'rgba(255,255,255,0.08)';
      ctx.fill();

      ctx.beginPath();
      ctx.arc(topologyNode.x, topologyNode.y, radius, 0, 2 * Math.PI, false);
      ctx.fillStyle = fill;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(topologyNode.x, topologyNode.y, radius, 0, 2 * Math.PI, false);
      ctx.lineWidth = 2 / Math.max(globalScale, 0.8);
      ctx.strokeStyle = palette.surface;
      ctx.stroke();

      if (globalScale > 0.45) {
        ctx.font = `${fontSize}px "Segoe UI", sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const textWidth = ctx.measureText(label).width;
        const pillWidth = textWidth + 16;
        const pillHeight = fontSize + 10;
        const pillX = topologyNode.x - pillWidth / 2;
        const pillY = topologyNode.y + radius + 8;

        ctx.shadowBlur = 0;
        ctx.fillStyle = palette.surface;
        ctx.strokeStyle = palette.border;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(pillX, pillY, pillWidth, pillHeight, 999);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = palette.text;
        ctx.fillText(label, topologyNode.x, pillY + pillHeight / 2);
      }

      ctx.shadowBlur = 0;
    },
    [hoveredNode, t]
  );

  const linkPaint = useCallback(
    (
      link: {
        source: TopologyNode & { x: number; y: number };
        target: TopologyNode & { x: number; y: number };
      },
      ctx: CanvasRenderingContext2D,
      globalScale: number
    ) => {
      const palette = readPalette();
      const source = link.source;
      const target = link.target;

      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.strokeStyle = `${palette.accent}33`;
      ctx.lineWidth = Math.max(1, 2 / globalScale);
      ctx.stroke();
    },
    []
  );

  return (
    <div ref={containerRef} className="h-full min-h-[42rem] overflow-hidden rounded-[1.5rem]">
      <ForceGraph2D
        ref={graphRef}
        cooldownTicks={110}
        d3AlphaDecay={0.018}
        d3VelocityDecay={0.38}
        graphData={data}
        height={dimensions.height}
        linkCanvasObject={linkPaint}
        linkColor={() => 'rgba(10, 100, 216, 0.2)'}
        linkDirectionalArrowColor={() => 'rgba(10, 100, 216, 0.35)'}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        linkWidth={1.2}
        nodeCanvasObject={nodePaint}
        nodeLabel="label"
        nodeRelSize={7}
        onEngineStop={() => {
          if (graphRef.current && data.nodes.length > 0) {
            graphRef.current.zoomToFit(400, 40);
          }
        }}
        onNodeClick={(node) => onNodeClick(node as unknown as TopologyNode)}
        onNodeHover={(node) =>
          setHoveredNode(node as unknown as TopologyNode | null)
        }
        width={dimensions.width}
      />
    </div>
  );
};
