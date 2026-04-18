import React, { useState, useRef, useEffect } from 'react';
import { attackService, AttackType } from '../../lib/services/attack';
import { AttackStatus, Device } from '../../types/device';
import { ShieldOff, AlertTriangle, Zap, Radio, ChevronDown, Network, Globe, RefreshCw, Activity, Wifi, Layers } from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { getAttackTypeDescription, getAttackTypeLabel } from '../../lib/attackTypeI18n';

interface AttackControlProps {
  device: Device;
  className?: string;
}

// Attack type metadata for UI
const attackTypeMetadata: Record<AttackType, { icon: React.ReactNode; color: string }> = {
  [AttackType.KICK]: {
    icon: <Zap className="h-4 w-4" />,
    color: '#ffaa44',
  },
  [AttackType.BLOCK]: {
    icon: <Radio className="h-4 w-4" />,
    color: '#9a4dff',
  },
  [AttackType.DHCP_SPOOF]: {
    icon: <Network className="h-4 w-4" />,
    color: '#0078d4',
  },
  [AttackType.DNS_SPOOF]: {
    icon: <Globe className="h-4 w-4" />,
    color: '#00bcf2',
  },
  [AttackType.ICMP_REDIRECT]: {
    icon: <RefreshCw className="h-4 w-4" />,
    color: '#8764b8',
  },
  [AttackType.PORT_SCAN]: {
    icon: <Activity className="h-4 w-4" />,
    color: '#107c10',
  },
  [AttackType.TRAFFIC_SHAPE]: {
    icon: <Layers className="h-4 w-4" />,
    color: '#ff8c00',
  },
  [AttackType.MAC_FLOOD]: {
    icon: <Network className="h-4 w-4" />,
    color: '#e81123',
  },
  [AttackType.VLAN_HOP]: {
    icon: <Layers className="h-4 w-4" />,
    color: '#737373',
  },
  [AttackType.BEACON_FLOOD]: {
    icon: <Wifi className="h-4 w-4" />,
    color: '#ffaa44',
  },
};

export const AttackControl: React.FC<AttackControlProps> = ({ device, className }) => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [selectedType, setSelectedType] = useState<AttackType | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const isUnderAttack = device.attack_status === AttackStatus.RUNNING;

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
        setSelectedType(null);
      }
    };

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showMenu]);

  const handleAttackClick = () => {
    if (isUnderAttack) {
      stopAttack();
    } else {
      setShowMenu(!showMenu);
    }
  };

  const handleSelectType = (type: AttackType) => {
    setSelectedType(type);
  };

  const confirmAttack = async () => {
    if (!selectedType) return;

    setIsLoading(true);
    setShowMenu(false);
    const toastId = toast.loading(
      t('attack.launching', {
        target: device.mac,
        type: getAttackTypeLabel(t, selectedType),
      })
    );

    try {
      await attackService.startAttack(device.mac, selectedType, 60);
      toast.success(t('attack.started', { type: getAttackTypeLabel(t, selectedType) }), {
        id: toastId,
      });
      setSelectedType(null);
    } catch (error: unknown) {
      console.error(error);
      toast.error(t('attack.startFailed'), { id: toastId });
    } finally {
      setIsLoading(false);
    }
  };

  const stopAttack = async () => {
    setIsLoading(true);
    const toastId = toast.loading(t('attack.stopping'));

    try {
      await attackService.stopAttack(device.mac);
      toast.success(t('attack.stopped'), { id: toastId });
    } catch (error: unknown) {
      console.error(error);
      toast.error(t('attack.stopFailed'), { id: toastId });
    } finally {
      setIsLoading(false);
    }
  };

  // Note: Removed safety check - allow attack on any device for research purposes
  // Users should be aware of risks when attacking gateway/router

  if (isUnderAttack) {
    return (
      <button
        onClick={stopAttack}
        disabled={isLoading}
        className={clsx(
          "btn-winui inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg text-white transition-all duration-200",
          isLoading && "opacity-50 cursor-not-allowed",
          className
        )}
        style={{
          backgroundColor: isLoading ? 'var(--winui-accent)' : '#d13438',
          minHeight: '24px'
        }}
        onMouseEnter={(e) => {
          if (!isLoading) e.currentTarget.style.backgroundColor = '#c12a2e';
        }}
        onMouseLeave={(e) => {
          if (!isLoading) e.currentTarget.style.backgroundColor = '#d13438';
        }}
      >
        {isLoading ? (
          <span className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-1.5" />
        ) : (
          <ShieldOff className="mr-1.5 h-3 w-3" />
        )}
        {t('attack.stop')}
      </button>
    );
  }

  return (
    <div className={clsx("relative inline-block text-left", className)} ref={menuRef}>
      <button
        onClick={handleAttackClick}
        disabled={isLoading}
        className="btn-winui-secondary inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200"
        style={{ minHeight: '24px' }}
      >
        <AlertTriangle className="mr-1.5 h-3 w-3" style={{ color: '#ffaa44' }} />
        {t('attack.attack')}
        <ChevronDown className="ml-1 h-3 w-3" style={{ color: 'var(--winui-text-tertiary)' }} />
      </button>

      {showMenu && (
        <div
          className="origin-top-right absolute right-0 mt-2 w-72 rounded-lg z-50"
          style={{
            backgroundColor: 'var(--winui-surface)',
            boxShadow: 'var(--winui-shadow-lg)',
            border: '1px solid var(--winui-border-subtle)'
          }}
        >
          {selectedType === null ? (
            // Attack type selection menu
            <div className="py-2 max-h-96 overflow-y-auto" role="menu">
              <div className="px-4 py-2 border-b" style={{ borderColor: 'var(--winui-border-subtle)' }}>
                <h3 className="text-xs font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{t('attackMenu.selectTypeTitle')}</h3>
                <p className="text-[10px] mt-0.5" style={{ color: 'var(--winui-text-secondary)' }}>{t('attackMenu.selectTypeDesc')}</p>
              </div>
              {Object.entries(attackTypeMetadata).map(([type, metadata]) => (
                <button
                  key={type}
                  onClick={() => handleSelectType(type as AttackType)}
                  className="w-full text-left px-4 py-2.5 text-xs flex items-center transition-colors duration-150 rounded-lg mx-1"
                  style={{ color: 'var(--winui-text-primary)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--winui-bg-tertiary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                  role="menuitem"
                >
                  <span style={{ color: metadata.color, marginRight: '8px' }}>
                    {metadata.icon}
                  </span>
                  <div className="flex-1">
                    <span className="font-semibold block">{getAttackTypeLabel(t, type as AttackType)}</span>
                    <span className="text-[10px]" style={{ color: 'var(--winui-text-tertiary)' }}>
                      {getAttackTypeDescription(t, type as AttackType)}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            // Confirmation menu
            <div className="py-2" role="menu">
              <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--winui-border-subtle)' }}>
                <h3 className="text-xs font-semibold mb-1" style={{ color: 'var(--winui-text-primary)' }}>{t('attackMenu.confirmTitle')}</h3>
                <div className="flex items-center space-x-2">
                  <span style={{ color: attackTypeMetadata[selectedType].color }}>
                    {attackTypeMetadata[selectedType].icon}
                  </span>
                  <div>
                    <div className="text-xs font-medium" style={{ color: 'var(--winui-text-primary)' }}>
                      {getAttackTypeLabel(t, selectedType)}
                    </div>
                    <div className="text-[10px]" style={{ color: 'var(--winui-text-secondary)' }}>
                      {getAttackTypeDescription(t, selectedType)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="px-4 py-3 space-y-2">
                <div className="text-[10px]" style={{ color: 'var(--winui-text-tertiary)' }}>
                  {t('attackMenu.target')}: <span className="font-mono">{device.mac}</span>
                </div>
                <div className="text-[10px]" style={{ color: 'var(--winui-text-tertiary)' }}>
                  {t('attackMenu.duration')}: {t('attackMenu.durationValue', { seconds: 60 })}
                </div>
                <div className="flex space-x-2 pt-2">
                  <button
                    onClick={() => setSelectedType(null)}
                    className="flex-1 btn-winui-secondary text-xs py-2 px-3 rounded-lg"
                    style={{ minHeight: '28px' }}
                  >
                    {t('common.back')}
                  </button>
                  <button
                    onClick={confirmAttack}
                    disabled={isLoading}
                    className="flex-1 btn-winui text-xs py-2 px-3 rounded-lg text-white"
                    style={{
                      backgroundColor: '#d13438',
                      minHeight: '28px'
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading) e.currentTarget.style.backgroundColor = '#c12a2e';
                    }}
                    onMouseLeave={(e) => {
                      if (!isLoading) e.currentTarget.style.backgroundColor = '#d13438';
                    }}
                  >
                    {t('common.confirm')}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
