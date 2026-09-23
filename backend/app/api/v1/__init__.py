from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.products import router as products_router
from app.api.v1.cart import router as cart_router
from app.api.v1.checkout import router as checkout_router
from app.api.v1.orders import router as orders_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.admin import router as admin_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(cart_router)
api_router.include_router(checkout_router)
api_router.include_router(orders_router)
api_router.include_router(inventory_router)
api_router.include_router(recommendations_router)
api_router.include_router(notifications_router)
api_router.include_router(admin_router)
