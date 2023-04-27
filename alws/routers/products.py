import typing

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from alws import database
from alws.auth import get_current_user
from alws.crud import products
from alws.dependencies import get_db
from alws.models import User
from alws.schemas import product_schema


public_router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@public_router.get(
    "/",
    response_model=typing.Union[
        typing.List[product_schema.Product],
        product_schema.ProductResponse
    ]
)
async def get_products(
    pageNumber: int = None,
    search_string: str = None,
    db: database.Session = Depends(get_db),
):
    return await products.get_products(
        db, page_number=pageNumber, search_string=search_string)


@public_router.post("/", response_model=product_schema.Product)
async def create_product(
    product: product_schema.ProductCreate,
    db: database.Session = Depends(get_db),
):
    async with db.begin():
        db_product = await products.create_product(db, product)
        await db.commit()
    await db.refresh(db_product)
    return await products.get_products(db, product_id=db_product.id)


@public_router.get("/{product_id}/", response_model=product_schema.Product)
async def get_product(
    product_id: int,
    db: database.Session = Depends(get_db),
):
    db_product = await products.get_products(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with {product_id=} is not found"
        )
    return db_product


@public_router.post(
    "/add/{build_id}/{product}/",
    response_model=product_schema.ProductOpResult
)
async def add_to_product(
    product: str,
    build_id: int,
    db: database.Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        await products.modify_product(
            db, build_id, product, user.id, "add")
        return product_schema.ProductOpResult(
            success=True,
            message=f"Build {build_id} is being added to product {product}")
    except Exception as exc:
        raise HTTPException(
            detail=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST)


@public_router.post(
    "/remove/{build_id}/{product}/",
    response_model=product_schema.ProductOpResult
)
async def remove_from_product(
    product: str,
    build_id: int,
    db: database.Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        await products.modify_product(
            db, build_id, product, user.id, "remove")
        return product_schema.ProductOpResult(
            success=True,
            message=f"Build {build_id} is being removed from product {product}")
    except Exception as exc:
        raise HTTPException(
            detail=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST)


@public_router.delete(
    "/{product_id}/remove/",
    response_model=product_schema.ProductOpResult
)
async def remove_product(
    product_id: int,
    db: database.Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        await products.remove_product(db, product_id, user.id)
        return product_schema.ProductOpResult(
            success=True,
            message=f"Product with {product_id=} successfully removed")
    except Exception as exc:
        raise HTTPException(
            detail=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST)
