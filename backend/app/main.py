import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import auth, dashboard, transactions
from app.bot.bot_instance import bot, dp
from app.bot.handlers import callback, start
from app.core.config import settings
from app.core.database import Base, engine
from app.services.eskiz_sms import sms
from app.services.reminder_engine import create_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    polling = None
    scheduler = None
    leader = None
    app.state.polling = None
    try:
        async with engine.begin() as connection:
            await connection.execute(text("SELECT 1"))
            if settings.AUTO_CREATE_TABLES:
                await connection.run_sync(Base.metadata.create_all)
        if settings.RUN_BOT or settings.RUN_SCHEDULER:
            leader = await engine.connect()
            locked = await leader.scalar(text("SELECT pg_try_advisory_lock(716293047)"))
            await leader.commit()
            if not locked:
                raise RuntimeError("Bot va eslatmalar uchun faqat bitta jarayon ishga tushirilishi kerak")
        if settings.RUN_BOT:
            dp.include_router(start.router)
            dp.include_router(callback.router)
            await bot.delete_webhook(drop_pending_updates=False)
            polling = asyncio.create_task(dp.start_polling(
                bot, handle_signals=False, close_bot_session=False,
                allowed_updates=dp.resolve_used_update_types()), name="telegram_polling")
            app.state.polling = polling
        if settings.RUN_SCHEDULER:
            scheduler = create_scheduler()
            scheduler.start()
        yield
    finally:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)
            await asyncio.sleep(0)
        if polling is not None:
            polling.cancel()
            with suppress(asyncio.CancelledError):
                await polling
        await sms.close()
        await bot.session.close()
        if leader is not None:
            with suppress(Exception):
                await leader.execute(text("SELECT pg_advisory_unlock(716293047)"))
                await leader.commit()
            await leader.close()
        await engine.dispose()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan,
              docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
              redoc_url=None, openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_credentials=False, allow_methods=["GET", "POST"],
                   allow_headers=["Authorization", "Content-Type"])


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Kiritilgan ma'lumotlarni tekshiring: summa, sana yoki telefon raqami noto'g'ri."})


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/health", tags=["Holat"])
async def health():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        task = app.state.polling
        if task is not None and task.done():
            return JSONResponse(status_code=503, content={"status": "Bot ishlamayapti"})
        return {"status": "Tayyor"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "Ma'lumotlar bazasi mavjud emas"})


app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
