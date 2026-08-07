from app.bot.routers.access import router as access_router
from app.bot.routers.admin import router as admin_router
from app.bot.routers.anime import router as anime_router
from app.bot.routers.common import router as common_router
from app.bot.routers.subscriptions import router as subscriptions_router
from app.bot.routers.trace import router as trace_router


def all_routers():
    # Access is first so channel membership rules are always active.
    return [access_router, common_router, anime_router, subscriptions_router, trace_router, admin_router]
