from typing import Any

from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput, TextInput
from aiogram_dialog.widgets.kbd import RequestContact
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
from aiogram_dialog.widgets.text import Const
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_user
from filters.chat_types import UserAuth
from kbds.inline import MenuCallbackData

dialogs_router = Router()
dialogs_router.callback_query.filter(UserAuth())


class UserSG(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()


# Проверка длины текста от 3 до 120 включительно
def name_check(text: Any) -> str:
    if all(not ch.isdigit() for ch in text) and 3 <= len(text) <= 120:
        return text
    raise ValueError


# Хэндлер, который сработает, если пользователь ввел корректное имя
async def correct_first_name_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str) -> None:
    dialog_manager.dialog_data.update(first_name=text)
    await dialog_manager.next()


# Хэндлер, который сработает на ввод некорректного имени
async def error_first_name_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    await message.answer(
        text='Ты ввел некорректное имя. Попробуйте еще раз'
    )


# Хэндлер, который сработает, если пользователь ввел корректную фамилию
async def correct_last_name_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str) -> None:
    dialog_manager.dialog_data.update(last_name=text)
    await dialog_manager.next()


# Хэндлер, который сработает на ввод некорректной фамилии
async def error_last_name_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    await message.answer(
        text='Ты ввел некорректную фамилию. Попробуйте еще раз'
    )


# Хэндлер, который сработает, если пользователь отправил вообще не текст
async def no_text(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    print(type(widget))
    await message.answer(text='Ты ввел вообще не текст!')


async def check_phone(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    if message.from_user.id == message.contact.user_id:
        dialog_manager.dialog_data.update(phone=message.contact.phone_number, user_id=message.from_user.id)
        await orm_add_user(dialog_manager.middleware_data['session'], dialog_manager.dialog_data)
        await dialog_manager.done()
        await message.answer('Спасибо! Твои данные сохранены 👍')


start_dialog = Dialog(
    Window(
        Const(text='Для того чтобы оставлять прогнозы и участвовать в турнире оставь данные о себе 👇'
                   '\n\nВведи свое имя'),
        TextInput(
            id='first_name_input',
            type_factory=name_check,
            on_success=correct_first_name_handler,
            on_error=error_first_name_handler,
        ),
        MessageInput(
            func=no_text,
            content_types=ContentType.ANY
        ),
        state=UserSG.first_name,
    ),
    Window(
        Const(text='Ок! Введи свою фамилию'),
        TextInput(
            id='last_name_input',
            type_factory=name_check,
            on_success=correct_last_name_handler,
            on_error=error_last_name_handler,
        ),
        MessageInput(
            func=no_text,
            content_types=ContentType.ANY
        ),
        state=UserSG.last_name,
    ),
    Window(
        Const(text='Супер! Осталось отправить номер телефона. Нажми кнопку 👇'),
        RequestContact(Const("👤 Отправить номер телефона")),
        MessageInput(
            func=check_phone,
            content_types=ContentType.CONTACT
        ),
        markup_factory=ReplyKeyboardFactory(
            input_field_placeholder=Const('Сообщение'),
            resize_keyboard=True,
        ),
        state=UserSG.phone
    )
)


# Это классический хэндлер на команду /start
@dialogs_router.callback_query(MenuCallbackData.filter(F.menu_name == 'my_forecasts'))
async def command_start_process(callback: types.CallbackQuery, callback_data: MenuCallbackData,
                                dialog_manager: DialogManager, session: AsyncSession):
    await dialog_manager.start(state=UserSG.first_name, mode=StartMode.RESET_STACK)
