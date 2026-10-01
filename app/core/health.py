import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.redis import redis_client
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])

DBSession = Annotated[Session, Depends(get_db)]


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check(response: Response, db: DBSession) -> dict[str, str]:
    is_ready = True

    try:
        _ = db.execute(text("SELECT 1"))
    except SQLAlchemyError as e:
        logger.error("PostgreSQL readiness check failed: %s", e)
        is_ready = False

    try:
        _ = redis_client.ping()
    except RedisError as e:
        logger.error("Redis readiness check failed: %s", e)
        is_ready = False

    if is_ready:
        return {"status": "ready"}

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not_ready"}
