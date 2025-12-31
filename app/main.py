from fastapi import FastAPI
print("salam")
app = FastAPI(title="Hunter Agent")

@app.get("/health")
def health():
    return {"status": "ok"}
