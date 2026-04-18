import { TFunction } from 'i18next';
import { AttackType } from './services/attack';

const attackTypeKeyMap: Record<AttackType, string> = {
  [AttackType.KICK]: 'kick',
  [AttackType.BLOCK]: 'block',
  [AttackType.DHCP_SPOOF]: 'dhcp_spoof',
  [AttackType.DNS_SPOOF]: 'dns_spoof',
  [AttackType.ICMP_REDIRECT]: 'icmp_redirect',
  [AttackType.PORT_SCAN]: 'port_scan',
  [AttackType.TRAFFIC_SHAPE]: 'traffic_shape',
  [AttackType.MAC_FLOOD]: 'mac_flood',
  [AttackType.VLAN_HOP]: 'vlan_hop',
  [AttackType.BEACON_FLOOD]: 'beacon_flood',
};

export const getAttackTypeLabel = (t: TFunction, type: AttackType) =>
  t(`attack.types.${attackTypeKeyMap[type]}.label`);

export const getAttackTypeDescription = (t: TFunction, type: AttackType) =>
  t(`attack.types.${attackTypeKeyMap[type]}.description`);
