from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import structlog
import time
from datetime import datetime

from api.routers import ocr, classify, ner, advise, auth
from api.database import create_db_and_tables
from api.auth import get_user_db
from api.models.schemas import UserCreate, UserRead, UserUpdate
from api.models.user import UserRole
from .rag_service import get_rag_status

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Legal ASI Platform...")
    await create_db_and_tables()
    logger.info("Database tables created")
    yield
    # Shutdown
    logger.info("Shutting down Legal ASI Platform...")

app = FastAPI(
    title="Legal ASI - AI-Powered Legal Document Analysis",
    description="""
    Legal ASI platform for Russian legal document processing with:
    
    - **Authentication**: JWT-based auth with role-based access control
    - **OCR**: Text extraction from scanned documents
    - **Classification**: Document type identification (bills, fines, protocols)
    - **NER**: Named entity recognition for legal entities
    - **Advisory**: AI-powered legal analysis and recommendations
    
    Enhanced with pattern matching, confidence calibration, and Russian language optimization.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(classify.router, prefix="/api/v1/classify", tags=["Classification"])
app.include_router(ner.router, prefix="/api/v1/ner", tags=["Named Entity Recognition"])
app.include_router(advise.router, prefix="/api/v1/advise", tags=["Legal Advisory"])

@app.get("/health")
async def health_check():
    """Enhanced health check including RAG service"""
    rag_status = get_rag_status()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-preGPU",
        "services": {
            "api": "active",
            "database": "active",  # TODO: Add actual DB health check
            "rag": rag_status["status"],
            "rag_documents": rag_status.get("document_count", 0)
        },
        "features": {
            "ocr": True,
            "classification": True,
            "ner": True,
            "llm_advisory": True,
            "rag_search": rag_status["status"] == "active",
            "authentication": True
        }
    }

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "Legal ASI - AI-Powered Legal Document Analysis Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "authentication": "/api/v1/auth",
        "api_endpoints": {
            "auth": {
                "login": "/api/v1/auth/jwt/login",
                "register": "/api/v1/auth/register",
                "me": "/api/v1/auth/me"
            },
            "ocr": "/api/v1/ocr/extract",
            "classify": "/api/v1/classify/document",
            "ner": "/api/v1/ner/extract",
            "advise": "/api/v1/advise/analyze"
        }
    }

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    
    logger.info(
        "Request received",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time, 3)
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 