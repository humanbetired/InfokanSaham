from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import predict, sentiment, market, backtest

app = FastAPI(
    title="InfokanSaham API",
    description="Stock Intelligence Platform untuk Saham IDX",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(sentiment.router)
app.include_router(market.router)
app.include_router(backtest.router)

@app.get("/")
def root():
    return {
        "app": "InfokanSaham",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "healthy"}