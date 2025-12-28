from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.topology import NetworkTopology
from app.repositories.device import DeviceRepository
from app.services.state import StateManager, get_state_manager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/topology", tags=["topology"])


@router.get("", response_model=NetworkTopology)
async def get_topology(
    db: AsyncSession = Depends(get_db),
    state: StateManager = Depends(get_state_manager),
):
    """Get the current network topology from database devices."""
    # Load devices from database to update state
    repo = DeviceRepository(db)
    db_devices = await repo.get_all()
    
    # Sync devices to in-memory state (for topology generation)
    for device in db_devices:
        state.update_device(device)
    
    # Generate topology from state
    return state.get_topology()
