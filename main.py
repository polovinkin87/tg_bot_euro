import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_dialog import setup_dialogs
from aiogram.fsm.storage.redis import RedisStorage, Redis, DefaultKeyBuilder

from dotenv import find_dotenv, load_dotenv

from dialogs.all_forecasts import dialog_forecast_router, forecast_start_dialog, forecast_second_dialog
from dialogs.user_data import start_dialog, dialogs_router
from kbds.menu import set_main_menu

load_dotenv(find_dotenv())

from middlewares.db import DataBaseSession

from database.engine import create_db, drop_db, session_maker

from handlers.user_private import user_private_router
from handlers.user_group import user_group_router
from handlers.admin_private import admin_router

# from common.bot_cmds_list import private
# ALLOWED_UPDATES = ['message', 'edited_message', 'callback_query']

redis = Redis(host='tg_bot_euro-redis_fsm-1')
storage: RedisStorage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_destiny=True))

bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot.my_admins_list = []

dp = Dispatcher(storage=storage)

dp.include_router(dialogs_router)
dp.include_router(start_dialog)
dp.include_router(dialog_forecast_router)
dp.include_router(forecast_start_dialog)
dp.include_router(forecast_second_dialog)
setup_dialogs(dp)
dp.include_router(user_private_router)
dp.include_router(user_group_router)
dp.include_router(admin_router)


async def on_startup(bot):
    # await drop_db()
    print('бот завелся')
    await create_db()


async def on_shutdown(bot):
    print('бот лег')


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.startup.register(set_main_menu)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    # await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


logging.basicConfig(level=logging.INFO)
asyncio.run(main())
