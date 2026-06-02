"""Job state management. Firestore in production, in-memory for local dev."""

import logging
import os
import uuid
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

_local_store: dict[str, dict] = {}
_firestore_client = None


def _get_firestore():
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    if os.getenv("FIRESTORE_EMULATOR_HOST") or os.getenv("GOOGLE_CLOUD_PROJECT"):
        try:
            from google.cloud import firestore

            db_name = os.getenv("FIRESTORE_DATABASE", "(default)")
            _firestore_client = firestore.Client(database=db_name)
            logger.info("Firestore initialized (database=%s)", db_name)
            return _firestore_client
        except Exception as e:
            logger.warning("Firestore unavailable, using in-memory: %s", e)
            return None
    return None


def _collection():
    client = _get_firestore()
    if client:
        return client.collection("jobs")
    return None


def create_job(project_url: str, target_branch: str) -> str:
    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "status": "pending",
        "project_url": project_url,
        "target_branch": target_branch,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "scan_result": None,
        "detection_result": None,
        "generation_result": None,
        "error": None,
    }

    col = _collection()
    if col:
        col.document(job_id).set(job_data)
    else:
        _local_store[job_id] = job_data

    return job_id


def get_job(job_id: str) -> dict | None:
    col = _collection()
    if col:
        doc = col.document(job_id).get()
        return doc.to_dict() if doc.exists else None
    return _local_store.get(job_id)


def update_job(job_id: str, **kwargs) -> None:
    kwargs["updated_at"] = datetime.now(UTC).isoformat()
    col = _collection()
    if col:
        col.document(job_id).update(kwargs)
    else:
        if job_id in _local_store:
            _local_store[job_id].update(kwargs)
