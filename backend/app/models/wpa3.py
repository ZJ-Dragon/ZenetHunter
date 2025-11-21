"""WPA3/802.1X Access Control Configuration Models."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class WpaMode(str, Enum):
    """WPA Security Mode."""

    WPA3_PERSONAL = "wpa3_personal"
    WPA3_ENTERPRISE = "wpa3_enterprise"
    WPA2_WPA3_MIXED = "wpa2_wpa3_mixed"


class EapMethod(str, Enum):
    """EAP Authentication Methods for 802.1X."""

    PEAP = "peap"
    TLS = "tls"
    TTLS = "ttls"


class RadiusConfig(BaseModel):
    """RADIUS Server Configuration."""

    server_ip: IPvAnyAddress = Field(..., description="RADIUS server IP address")
    port: int = Field(default=1812, ge=1, le=65535, description="RADIUS auth port")
    secret: str = Field(..., description="RADIUS shared secret")

    model_config = ConfigDict(from_attributes=True)


class VlanPolicy(BaseModel):
    """VLAN Assignment Policy."""

    vlan_id: int = Field(..., ge=1, le=4094, description="VLAN ID")
    name: str = Field(..., description="VLAN name/description")
    # Future: QoS, ACL rules per VLAN

    model_config = ConfigDict(from_attributes=True)


class Wpa3Config(BaseModel):
    """WPA3/802.1X Configuration."""

    mode: WpaMode = Field(
        default=WpaMode.WPA3_ENTERPRISE, description="WPA security mode"
    )
    ssid: str = Field(..., description="Wireless network SSID")
    radius: RadiusConfig | None = Field(
        None, description="RADIUS configuration (required for Enterprise mode)"
    )
    eap_method: EapMethod | None = Field(
        None, description="EAP method (required for Enterprise mode)"
    )
    # VLAN assignment based on user role/identity
    default_vlan: VlanPolicy | None = Field(
        None, description="Default VLAN for authenticated users"
    )

    model_config = ConfigDict(from_attributes=True)
