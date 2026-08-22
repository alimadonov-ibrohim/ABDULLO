from aiogram import Router

from .admin import router as admin_router
from .analysis import router as analysis_router
from .fallback import router as fallback_router
from .start_menu import router as start_router
from .vip import router as vip_router


def get_routers() -> list[Router]:
    return [
        admin_router,
        start_router,
        vip_router,
        analysis_router,
        fallback_router,
    ]


__all__ = ["get_routers"]
