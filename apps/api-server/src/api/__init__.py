from .admin import router as admin
from .cart import router as cart
from .categories import router as categories
from .chat import router as chat
from .favorites import router as favorites
from .geo import router as geo
from .notifications import router as notifications
from .orders import router as orders
from .owner import router as owner
from .payments import router as payments
from .payments_v2 import router as payments_v2
from .products import router as products
from .profile import router as profile
from .promotions import router as promotions
from .reports import router as reports
from .reviews import router as reviews
from .search import router as search
from .shipping import router as shipping
from .store_locator import router as store_locator
from .stores import router as stores
from .tasks import router as tasks
from .voice import router as voice
from .websocket import router as websocket

__all__ = [
    "admin",
    "cart",
    "categories",
    "chat",
    "favorites",
    "geo",
    "notifications",
    "orders",
    "owner",
    "payments",
    "payments_v2",
    "products",
    "profile",
    "promotions",
    "reports",
    "reviews",
    "search",
    "shipping",
    "store_locator",
    "stores",
    "tasks",
    "voice",
    "websocket",
]
