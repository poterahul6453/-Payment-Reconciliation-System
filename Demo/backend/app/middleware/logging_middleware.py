import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("reconciliation.api")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()
        logger.info("[%s] %s %s", request_id, request.method, request.url.path)
        try:
            response = await call_next(request)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("[%s] %s %s -> %d (%.1fms)", request_id, request.method, request.url.path, response.status_code, elapsed)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.exception("[%s] %s %s failed (%.1fms): %s", request_id, request.method, request.url.path, elapsed, exc)
            raise
