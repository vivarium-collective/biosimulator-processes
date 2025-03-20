import pytest
from unittest.mock import AsyncMock, MagicMock
from backend import MongoConnector
from backend.dispatch import JobProcessor, JobDispatcher

from tests.fixtures.membrane import membrane_request


@pytest.fixture
def mock_db():
    """Mock MongoDB connection with async methods."""
    mock_conn = MagicMock(spec=MongoConnector)
    mock_conn.get_jobs = AsyncMock(return_value=[])  # No initial jobs
    mock_conn.update_job = AsyncMock()
    mock_conn.write = AsyncMock()

    mock_conn.db = MagicMock()
    mock_conn.db.watch = MagicMock()

    return mock_conn


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_db", "membrane_request")
async def test_e2e_listener(mock_db, membrane_request):
    print('Running e2e test with request', membrane_request)

    dispatcher = JobDispatcher(conn=mock_db)
    dispatcher.processor = JobProcessor()

    mock_stream = AsyncMock()
    mock_stream.__enter__.return_value = mock_stream
    mock_stream.__iter__.return_value = iter([
        {"fullDocument": membrane_request}
    ])
    mock_db.db.watch.return_value = mock_stream

    await dispatcher.listen()

    mock_db.update_job.assert_any_call(job_id="test", status="IN_PROGRESS")
    mock_db.write.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_db", "membrane_request")
async def test_e2e_fallback(mock_db, membrane_request):
    print('Running e2e test with request', membrane_request)
    dispatcher = JobDispatcher(conn=mock_db)
    dispatcher.processor = JobProcessor()

    mock_db.get_jobs.return_value = [membrane_request]

    await dispatcher.fallback(buffer=1)

    # check job update
    mock_db.update_job.assert_any_call(job_id="test", status="IN_PROGRESS")

    # check write of update
    mock_db.write.assert_called_once()

    # call write
    job_update_args = mock_db.write.call_args[1]

    # ensure status update
    assert job_update_args["status"] == "COMPLETE"
    # ensure results (even if failed)
    assert "result" in job_update_args
