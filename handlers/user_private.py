from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_to_forecast, orm_get_game, orm_update_forecast, orm_check_user
from filters.chat_types import ChatTypeFilter
from handlers.menu_processing import get_menu_content

from kbds.inline import MenuCallbackData
from lexicon.lexicon import LEXICON

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


# Этот хэндлер будет срабатывать на команду "/start"
@user_private_router.message(CommandStart())
async def process_start_command(message: types.Message):
    await message.answer(LEXICON[message.text])


# Этот хэндлер будет срабатывать на команду "/help"
# и отправлять пользователю сообщение со списком доступных команд в боте
@user_private_router.message(Command(commands='help'))
async def process_help_command(message: types.Message):
    await message.answer(LEXICON[message.text])


@user_private_router.message(Command(commands='main'))
async def start_cmd(message: types.Message, session: AsyncSession, bot: Bot):
    media, reply_markup = await get_menu_content(session, level=0, menu_name=message.text)
    await message.answer_photo(photo=media.media, reply_markup=reply_markup)


class GetForecasts(StatesGroup):
    goals_owner = State()
    goals_guest = State()

    forecast_for_change = None


@user_private_router.callback_query(StateFilter(None), MenuCallbackData.filter(F.game_id))
async def get_forecasts(
        callback: types.CallbackQuery, callback_data: MenuCallbackData, state: FSMContext, session: AsyncSession):
    game = await orm_get_game(session, callback_data.game_id)
    user = await orm_check_user(session, callback_data.user_id)
    GetForecasts.forecast_for_change = game
    await callback.message.delete_reply_markup()
    await callback.message.answer(f'Введите кол-во голов {GetForecasts.forecast_for_change.owner}')
    await state.update_data(user_id=user.id, game_id=callback_data.game_id)
    await state.set_state(GetForecasts.goals_owner)


# Ловим данные для состояния goals_owner и потом меняем состояние на goals_guest
@user_private_router.message(GetForecasts.goals_owner, F.text)
async def input_owner_forecasts(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(owner=int(message.text))
        await message.answer(f'Введите кол-во голов {GetForecasts.forecast_for_change.guest}')
        await state.set_state(GetForecasts.goals_guest)
    else:
        await message.answer('К сожалению ты ввел не допустимые данные ☹️, введи число')
        await state.set_state(GetForecasts.goals_owner)


# Хендлер для отлова некорректных вводов для состояния goals_owner
@user_private_router.message(GetForecasts.goals_owner)
async def input_owner_forecasts2(message: types.Message, state: FSMContext):
    await message.answer('К сожалению ты ввел не допустимые данные ☹️, введи кол-во голов заново')


# Ловим данные для состояния goals_guest и потом выходим из состояний
@user_private_router.message(GetForecasts.goals_guest, F.text)
async def input_guest_forecasts(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text.isdigit():
        await state.update_data(guest=int(message.text))
        data = await state.get_data()
        media, reply_markup = await get_menu_content(session, level=0, menu_name="main")
        if await orm_add_to_forecast(session, data['user_id'], data['game_id'], data['owner'], data['guest']):
            await message.answer_photo(photo=media.media, caption="Прогноз добавлен", reply_markup=reply_markup)
        else:
            await message.answer_photo(photo=media.media, caption="Прогноз изменен", reply_markup=reply_markup)
        await state.clear()
        GetForecasts.forecast_for_change = None
    else:
        await message.answer('К сожалению ты ввел не допустимые данные ☹️, введи число')
        await state.set_state(GetForecasts.goals_guest)


# Хендлер для отлова некорректных вводов для состояния goals_guest
@user_private_router.message(GetForecasts.goals_guest)
async def input_guest_forecasts2(message: types.Message, state: FSMContext):
    await message.answer('К сожалению ты ввел не допустимые данные ☹️, введи кол-во голов заново')


@user_private_router.callback_query(MenuCallbackData.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallbackData, session: AsyncSession):
    print(callback_data.level, callback_data.menu_name, callback_data.group_id, callback_data.page,
          callback_data.game_id)
    media, reply_markup = await get_menu_content(session,
                                                 level=callback_data.level,
                                                 menu_name=callback_data.menu_name,
                                                 group_id=callback_data.group_id,
                                                 page=callback_data.page,
                                                 game_id=callback_data.game_id,
                                                 user_id=callback.from_user.id,
                                                 )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()

# @user_private_router.callback_query()
# async def test(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession, bot: Bot):
#     print(await bot.get_updates())
#     print(await bot.get_webhook_info())
#     print(callback_data.level, callback_data.menu_name)
#     await callback.answer(f'Ку')


# @user_private_router.message(F.photo)
# async def add_image(message: types.Message, session: AsyncSession):
#     if message.photo:
#         await message.answer(message.photo[-1].file_id)
#     else:
#         await message.answer("Отправьте фото пищи")
