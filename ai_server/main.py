from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analyze, embed

app = FastAPI(title="Missing Pet Finder AI Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/ai", tags=["analyze"])
app.include_router(embed.router, prefix="/ai", tags=["embed"])


@app.get("/health")
def health():
    return {"status": "ok"}
