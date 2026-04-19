import asyncio

from fastapi.testclient import TestClient

from app.core.database import get_session_factory
from app.repositories.event_log import EventLogRepository


def test_logs_api(client: TestClient):
    # Test empty logs
    response = client.get("/api/logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Add a log
    log_data = {"level": "INFO", "module": "test_module", "message": "Test log message"}
    response = client.post("/api/logs", json=log_data)
    assert response.status_code == 201

    # Verify log is present
    response = client.get("/api/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 1
    assert any(log["message"] == "Test log message" for log in logs)


def test_logs_api_includes_persisted_audit_entries(client: TestClient):
    async def seed_log():
        session_factory = get_session_factory()
        async with session_factory() as session:
            repo = EventLogRepository(session)
            await repo.add_log(
                level="warning",
                module="audit",
                message="Persisted audit entry",
                context={"source": "db"},
            )
            await session.commit()

    asyncio.run(seed_log())

    response = client.get("/api/logs")
    assert response.status_code == 200
    logs = response.json()
    assert any(log["message"] == "Persisted audit entry" for log in logs)
