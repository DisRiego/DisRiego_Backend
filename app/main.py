from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Infraestructura lista, backend en Render funcionando"}
