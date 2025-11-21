import { Device } from './device';

export interface TopologyNode {
  id: string;
  label: string;
  type: 'router' | 'device' | 'gateway';
  data: Device;
}

export interface TopologyLink {
  source: string;
  target: string;
  type: string;
}

export interface NetworkTopology {
  nodes: TopologyNode[];
  links: TopologyLink[];
}
