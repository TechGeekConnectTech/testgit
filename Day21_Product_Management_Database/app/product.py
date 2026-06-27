from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
def get_products():
    return JSONResponse(content={"message": "List of products"}, status_code=200)