from typing import Any

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window, ShowMode
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput, TextInput
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_game, orm_check_user, orm_get_forecasts, orm_update_forecast, \
    orm_add_forecast
from dialogs.state import EditForecasts, MyForecasts
from filters.chat_types import UserAuth

edit_forecasts_router = Router()


# Проверка числа
def name_check(text: Any) -> int:
    if text.isdigit():
        return int(text)
    raise ValueError


# Хэндлер, который сработает, если пользователь ввел корректное кол-во голов хозяев
async def correct_goals_owner_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str) -> None:
    dialog_manager.dialog_data.update(goals_owner=int(text))
    await dialog_manager.next()


# Хэндлер, который сработает на ввод некорректного кол-во голов хозяев
async def error_goals_owner_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    await message.answer(
        text='Ты ввел не число. Попробуй еще раз'
    )


# Хэндлер, который сработает, если пользователь ввел корректное кол-во голов гостей
async def correct_goals_guest_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str) -> None:
    session = dialog_manager.middleware_data['session']
    dialog_manager.dialog_data.update(goals_guest=int(text))
    user = await orm_check_user(session, dialog_manager.event.from_user.id)
    forecast = await orm_get_forecasts(session, user.id, dialog_manager.start_data.get('game_id'))
    if forecast:
        await orm_update_forecast(session, forecast.id, dialog_manager.dialog_data.get('goals_owner'),
                                  dialog_manager.dialog_data.get('goals_guest'))
        await message.answer("Прогноз изменен!")
    else:
        await orm_add_forecast(session, user.id, dialog_manager.start_data.get('game_id'),
                               dialog_manager.dialog_data.get('goals_owner'),
                               dialog_manager.dialog_data.get('goals_guest'))
        await message.answer("Прогноз добавлен!")
    await dialog_manager.start(state=MyForecasts.groups, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


# Хэндлер, который сработает на ввод некорректное кол-во голов гостей
async def error_goals_guest_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    await message.answer(
        text='Ты ввел не число. Попробуй еще раз'
    )


# Хэндлер, который сработает, если пользователь отправил вообще не текст
async def no_text(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    await message.answer(text='Ты ввел вообще не текст!')


async def getter_get_games(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    game = await orm_get_game(session, dialog_manager.start_data.get('game_id'))
    return {'owner': game.owner, 'guest': game.guest}


edit_forecasts_dialog = Dialog(
    Window(
        Format(text='Введите кол-во голов {owner}'),
        TextInput(
            id='goals_owner_input',
            type_factory=name_check,
            on_success=correct_goals_owner_handler,
            on_error=error_goals_owner_handler,
        ),
        MessageInput(
            func=no_text,
            content_types=ContentType.TEXT
        ),
        state=EditForecasts.goals_owner,
        getter=getter_get_games,
    ),
    Window(
        Format(text='Введите кол-во голов {guest}'),
        TextInput(
            id='goals_guest_input',
            type_factory=name_check,
            on_success=correct_goals_guest_handler,
            on_error=error_goals_guest_handler,
        ),
        MessageInput(
            func=no_text,
            content_types=ContentType.ANY
        ),
        state=EditForecasts.goals_guest,
        getter=getter_get_games,
    ),
)