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
  intensity?: number;
}

export const attackService = {
  /**
   * Start an active defense operation on a target device
   * @param mac Target device MAC address
   * @param type Attack type (kick, block, etc.)
   * @param duration Duration in seconds
   * @param intensity Intensity level 1-10 (default: 5)
   */
  startAttack: async (mac: string, type: AttackType = AttackType.KICK, duration: number = 60, intensity: number = 5) => {
    // API endpoint: POST /api/active-defense/{mac}/start
    const response = await api.post(`/active-defense/${mac}/start`, {
      type,
      duration,
      intensity
    });
    return response.data;
  },

  /**
   * Stop an active defense operation on a target device
   * @param mac Target device MAC address
   */
  stopAttack: async (mac: string) => {
    // API endpoint: POST /api/active-defense/{mac}/stop
    const response = await api.post(`/active-defense/${mac}/stop`);
    return response.data;
  },

  /**
   * Get available attack types
   */
  getAttackTypes: async () => {
    // API endpoint: GET /api/active-defense/types
    const response = await api.get('/active-defense/types');
    return response.data;
  },
};
