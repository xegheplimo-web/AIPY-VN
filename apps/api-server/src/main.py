from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api import search, stores, products, owner, admin, orders, cart, chat, shipping
from src.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="VietStore RAG API",
    description="AI-powered local e-commerce marketplace API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search)
app.include_router(stores)
app.include_router(products)
app.include_router(owner)
app.include_router(admin)
app.include_router(orders)
app.include_router(cart)
app.include_router(chat)
app.include_router(shipping.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
