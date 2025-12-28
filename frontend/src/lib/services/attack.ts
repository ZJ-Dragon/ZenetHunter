import { api } from '../api';

export enum AttackType {
  KICK = 'kick',  // WiFi Deauthentication/Disassociation
  BLOCK = 'block',  // ARP Spoofing / Man-in-the-Middle
  DHCP_SPOOF = 'dhcp_spoof',  // DHCP Spoofing (redirect to controlled server)
  DNS_SPOOF = 'dns_spoof',  // DNS Spoofing (redirect DNS queries)
  ICMP_REDIRECT = 'icmp_redirect',  // ICMP Redirect (route manipulation)
  PORT_SCAN = 'port_scan',  // Port Scanning (reconnaissance)
  TRAFFIC_SHAPE = 'traffic_shape',  // Traffic Shaping (bandwidth limiting)
  MAC_FLOOD = 'mac_flood',  // MAC Flooding (switch table exhaustion)
  VLAN_HOP = 'vlan_hop',  // VLAN Hopping (if applicable)
  BEACON_FLOOD = 'beacon_flood',  // WiFi Beacon Flood (AP confusion)
}

export interface AttackRequest {
  type: AttackType;
  duration: number;
}

export const attackService = {
  startAttack: async (mac: string, type: AttackType = AttackType.KICK, duration: number = 60) => {
    const response = await api.post(`/devices/${mac}/attack/start`, { type, duration });
    return response.data;
  },

  stopAttack: async (mac: string) => {
    const response = await api.post(`/devices/${mac}/attack/stop`);
    return response.data;
  },
};
