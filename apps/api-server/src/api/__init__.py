from .search import router as search
from .stores import router as stores
from .products import router as products
from .owner import router as owner
from .admin import router as admin
from .orders import router as orders
from .cart import router as cart
from .chat import router as chat
from .shipping import router as shipping
from .voice import router as voice
from .notifications import router as notifications
from .tasks import router as tasks
from .payments import router as payments
from .reviews import router as reviews
from .profile import router as profile
from .categories import router as categories
from .favorites import router as favorites
from .store_locator import router as store_locator

__all__ = [
    "search",
    "stores",
    "products",
    "owner",
    "admin",
    "orders",
    "cart",
    "chat",
    "shipping",
    "voice",
    "notifications",
    "tasks",
    "payments",
    "reviews",
    "profile",
    "categories",
    "favorites",
    "store_locator",
]
