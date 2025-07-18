#!/usr/bin/env python3
"""
Security Middleware for Legal AI API
Implements rate limiting, security headers, and request validation
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import redis
import asyncio

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        redis_url: Optional[str] = None,
        enabled: bool = True
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.enabled = enabled
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        
        # Initialize Redis if available
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Rate limiting using Redis backend")
            except Exception as e:
                logger.warning(f"Redis not available for rate limiting: {e}")
        
        # Fallback to in-memory storage
        if not self.redis_client:
            self.buckets = defaultdict(dict)
            logger.info("Rate limiting using in-memory backend")
    
    def _get_client_key(self, request: Request) -> str:
        """Generate client key for rate limiting"""
        # Use forwarded IP if behind proxy, otherwise remote address
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or request.client.host
        )
        
        # Add user ID if authenticated
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        return f"ip:{client_ip}"
    
    def _get_bucket_key(self, client_key: str, endpoint: str) -> str:
        """Generate bucket key for specific endpoint"""
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:8]
        return f"rate_limit:{client_key}:{endpoint_hash}"
    
    async def _check_rate_limit_redis(self, bucket_key: str) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis backend"""
        try:
            pipe = self.redis_client.pipeline()
            
            # Get current bucket state
            current_time = time.time()
            bucket_data = self.redis_client.hgetall(bucket_key)
            
            if bucket_data:
                last_refill = float(bucket_data.get(b'last_refill', current_time))
                tokens = float(bucket_data.get(b'tokens', self.burst_size))
            else:
                last_refill = current_time
                tokens = self.burst_size
            
            # Refill tokens based on time elapsed
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            tokens = min(self.burst_size, tokens + tokens_to_add)
            
            # Check if request can be served
            if tokens >= 1:
                tokens -= 1
                allowed = True
            else:
                allowed = False
            
            # Update bucket state
            pipe.hset(bucket_key, mapping={
                'tokens': tokens,
                'last_refill': current_time,
                'requests': int(bucket_data.get(b'requests', 0)) + (1 if allowed else 0)
            })
            pipe.expire(bucket_key, 3600)  # Expire after 1 hour
            pipe.execute()
            
            return allowed, {
                'tokens_remaining': int(tokens),
                'reset_time': int(current_time + (1 - tokens) / self.refill_rate) if tokens < 1 else None,
                'requests_per_minute': self.requests_per_minute
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fallback to allow request if Redis fails
            return True, {'error': 'rate_limit_check_failed'}
    
    async def _check_rate_limit_memory(self, bucket_key: str) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit using in-memory storage"""
        current_time = time.time()
        
        if bucket_key not in self.buckets:
            self.buckets[bucket_key] = {
                'tokens': self.burst_size,
                'last_refill': current_time,
                'requests': 0
            }
        
        bucket = self.buckets[bucket_key]
        
        # Refill tokens
        time_elapsed = current_time - bucket['last_refill']
        tokens_to_add = time_elapsed * self.refill_rate
        bucket['tokens'] = min(self.burst_size, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = current_time
        
        # Check if request can be served
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            bucket['requests'] += 1
            allowed = True
        else:
            allowed = False
        
        return allowed, {
            'tokens_remaining': int(bucket['tokens']),
            'reset_time': int(current_time + (1 - bucket['tokens']) / self.refill_rate) if bucket['tokens'] < 1 else None,
            'requests_per_minute': self.requests_per_minute
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client and endpoint keys
        client_key = self._get_client_key(request)
        endpoint = f"{request.method}:{request.url.path}"
        bucket_key = self._get_bucket_key(client_key, endpoint)
        
        # Check rate limit
        if self.redis_client:
            allowed, rate_info = await self._check_rate_limit_redis(bucket_key)
        else:
            allowed, rate_info = await self._check_rate_limit_memory(bucket_key)
        
        if not allowed:
            # Rate limit exceeded
            headers = {
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(rate_info.get('reset_time', 0)),
                "Retry-After": str(max(1, int((rate_info.get('reset_time', 0) - time.time()))))
            }
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "requests_per_minute": self.requests_per_minute,
                    "retry_after": headers["Retry-After"]
                },
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(rate_info.get('tokens_remaining', 0))
        
        if rate_info.get('reset_time'):
            response.headers["X-RateLimit-Reset"] = str(rate_info['reset_time'])
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: https:; "
                "frame-ancestors 'none'"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "accelerometer=(), "
                "gyroscope=()"
            )
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Remove server info
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests"""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request too large"}
            )
        
        # Validate Content-Type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"
            ]
            
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "Unsupported media type"}
                )
        
        # Check for suspicious patterns in URL
        suspicious_patterns = [
            "../", "..\\", "etc/passwd", "proc/", "windows/system32",
            "<script", "javascript:", "vbscript:", "onload=", "onerror="
        ]
        
        url_str = str(request.url).lower()
        for pattern in suspicious_patterns:
            if pattern in url_str:
                logger.warning(f"Suspicious request detected: {request.url} from {request.client.host}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request"}
                )
        
        return await call_next(request)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced request logging middleware"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Generate request ID
        request_id = hashlib.md5(f"{time.time()}{request.client.host}".encode()).hexdigest()[:8]
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", ""),
                "forwarded_for": request.headers.get("x-forwarded-for", "")
            }
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "response_size": response.headers.get("content-length", "unknown")
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2)
                },
                exc_info=True
            )
            
            raise

# Utility functions for middleware configuration
def create_rate_limit_middleware(
    requests_per_minute: int = 60,
    burst_size: int = 10,
    redis_url: Optional[str] = None,
    enabled: bool = True
) -> RateLimitMiddleware:
    """Factory function for rate limit middleware"""
    
    def middleware_factory(app):
        return RateLimitMiddleware(
            app=app,
            requests_per_minute=requests_per_minute,
            burst_size=burst_size,
            redis_url=redis_url,
            enabled=enabled
        )
    
    return middleware_factory

def get_security_middleware_stack():
    """Get complete security middleware stack"""
    return [
        RequestValidationMiddleware,
        SecurityHeadersMiddleware,
        LoggingMiddleware
    ] 