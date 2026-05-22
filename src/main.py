from fastapi import FastAPI

app = FastAPI(title="Med Lab Interpreter API")

@app.get("/")
def read_root():
    return {
        "status": "alive",
        "message": "HealthTech API ready for infrastructure tests"
    }