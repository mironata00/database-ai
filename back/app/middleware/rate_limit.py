from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from collections import defaultdict
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls=60, period=60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        client = request.client.host
        now = time.time()
        
        self.requests[client] = [r for r in self.requests[client] if now - r < self.period]
        
        if len(self.requests[client]) >= self.calls:
            raise HTTPException(status_code=429, detail="Too many requests")
        
        self.requests[client].append(now)
        response = await call_next(request)
        return response
