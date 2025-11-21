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
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 20);
    }
  }, [data]);

  // Node painting logic
  const nodePaint = useCallback((node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
    // Cast node to TopologyNode to access custom properties
    const topologyNode = node as unknown as TopologyNode & { x: number; y: number };
    const label = topologyNode.label;
    const fontSize = 12 / globalScale;
    const radius = 5;

    // Draw Node Circle
    ctx.beginPath();
    ctx.arc(topologyNode.x, topologyNode.y, radius, 0, 2 * Math.PI, false);

    // Color based on type or status
    if (topologyNode.data?.status === 'offline') {
      ctx.fillStyle = '#9ca3af'; // gray
    } else if (topologyNode.data?.status === 'blocked') {
      ctx.fillStyle = '#ef4444'; // red
    } else if (topologyNode.type === 'router') {
      ctx.fillStyle = '#8b5cf6'; // purple
    } else {
      ctx.fillStyle = '#0ea5e9'; // brand blue
    }

    ctx.fill();

    // Draw Label
    ctx.font = `${fontSize}px Sans-Serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#1f2937'; // gray-800
    ctx.fillText(label, topologyNode.x, topologyNode.y + radius + fontSize);
  }, []);

  return (
    <div ref={containerRef} className="w-full h-full min-h-[600px] bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      <ForceGraph2D
        ref={graphRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={data}
        nodeLabel="label"
        nodeCanvasObject={nodePaint}
        onNodeClick={(node) => onNodeClick(node as unknown as TopologyNode)}
        linkColor={() => '#cbd5e1'} // slate-300
        linkWidth={2}
      />
    </div>
  );
};
