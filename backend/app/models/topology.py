from typing import List

from pydantic import BaseModel, Field

from app.models.device import Device


class TopologyNode(BaseModel):
    """Node in the network topology."""
    id: str = Field(..., description="Unique identifier (usually MAC)")
    label: str = Field(..., description="Display label (Name or IP)")
    type: str = Field(..., description="Node type (router, device, etc.)")
    data: Device = Field(..., description="Full device data")


class TopologyLink(BaseModel):
    """Link between two nodes in the topology."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(default="ethernet", description="Link type")


class NetworkTopology(BaseModel):
    """Full network topology graph."""
    nodes: List[TopologyNode] = Field(default_factory=list, description="List of topology nodes")
    links: List[TopologyLink] = Field(default_factory=list, description="List of topology links")

