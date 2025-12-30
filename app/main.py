from fastapi import FastAPI

app = FastAPI(title="Hunter Agent")

@app.get("/health")
def health():
    return {"status": "ok"}
