"""In-memory sliding window rate limiter middleware for FastAPI."""

import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window IP-based rate limiter middleware.
    Protects endpoints against spam and denial of service.
    """

    def __init__(self, app):
        super().__init__(app)
        # Store timestamps of requests: { (ip, endpoint_category): [timestamps] }
        self.requests = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _clean_old_requests(self, key: tuple, now: float, window_seconds: float):
        self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = self._get_client_ip(request)
        now = time.time()

        # Define limits (max_requests, window_seconds)
        if "/api/analytics/compile" in path:
            limit = 3
            window = 600.0  # 3 requests per 10 minutes (heavy ML compilation)
            category = "compile"
        elif "/api/analytics/ai" in path:
            limit = 30
            window = 60.0  # 30 requests per minute
            category = "ai"
        elif "/api/analytics/dashboard" in path:
            limit = 60
            window = 60.0  # 60 requests per minute
            category = "dashboard"
        elif "/health" in path:
            limit = 120
            window = 60.0
            category = "health"
        else:
            limit = 100
            window = 60.0  # 100 requests per minute
            category = "default"

        key = (client_ip, category)
        self._clean_old_requests(key, now, window)

        if len(self.requests[key]) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": f"Rate limit exceeded for {category}. Please try again later.",
                    "retry_after_seconds": int(window - (now - self.requests[key][0])),
                },
                headers={"Retry-After": str(int(window))},
            )

        self.requests[key].append(now)

        response: Response = await call_next(request)

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
