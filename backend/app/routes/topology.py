from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.device import DeviceType
from app.models.topology import NetworkTopology
from app.repositories.device import DeviceRepository
from app.services.state import StateManager, get_state_manager

router = APIRouter(prefix="/topology", tags=["topology"])


@router.get("", response_model=NetworkTopology)
async def get_topology(
    db: AsyncSession = Depends(get_db),
    state: StateManager = Depends(get_state_manager),
):
    """Get the current network topology from database devices."""
    repo = DeviceRepository(db)
    db_devices = await repo.get_all()

    # Sync devices to in-memory state for downstream consumers
    for device in db_devices:
        state.update_device(device)

    # Build topology directly from current DB snapshot to avoid stale in-memory state
    nodes = []
    links = []
    gateway_mac = None

    for device in db_devices:
        node_type = "device"
        if device.type == DeviceType.ROUTER:
            node_type = "router"
            gateway_mac = device.mac.lower()
        nodes.append(
            {
                "id": device.mac.lower(),
                "label": device.display_name or device.name or str(device.ip),
                "type": node_type,
                "data": device,
            }
        )

    if gateway_mac:
        for device in db_devices:
            mac = device.mac.lower()
            if mac != gateway_mac:
                links.append(
                    {
                        "source": gateway_mac,
                        "target": mac,
                        "type": "ethernet",
                    }
                )

    return NetworkTopology(nodes=nodes, links=links)
