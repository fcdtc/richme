from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from backend.routers import data, analysis, backtest


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting ETF Quantitative Trading Calculator API")
    yield
    # Shutdown
    print("Shutting down ETF Quantitative Trading Calculator API")


app = FastAPI(
    title="ETF Quantitative Trading Calculator",
    description="API for ETF technical analysis and trading signals",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "etf-calculator-api"}


# Register routers
app.include_router(data.router)
app.include_router(analysis.router)
app.include_router(backtest.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ETF Quantitative Trading Calculator API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
