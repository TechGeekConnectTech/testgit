from fastapi import FastAPI
from app import product, customer, auth


app = FastAPI(title="Product Management Database API", summary="This API is developed for product management database system", version="1.0")

app.include_router(auth.router)
app.include_router(product.router)
app.include_router(customer.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Product Management Database API!"}