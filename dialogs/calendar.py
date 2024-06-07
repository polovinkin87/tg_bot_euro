from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode, ShowMode, Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format, Const

from handlers.menu_processing import main_menu
from kbds.inline import MenuCallbackData

dialogs_calendar_router = Router()


class CalendarSG(StatesGroup):
    start = State()


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await callback.message.delete()
    media, reply_markup = await main_menu(level=0)
    await callback.message.answer_photo(photo=media.media, reply_markup=reply_markup)
    await callback.answer()


calendar_dialog = Dialog(
    Window(
        Const(text='Админ вчера выпил много пенного 🍻 - данная опция пока недоступна.'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked,
        ),
        state=CalendarSG.start,
    ),
)


# Это классический хэндлер на команду calendar
@dialogs_calendar_router.callback_query(MenuCallbackData.filter(F.menu_name == 'calendar'))
async def command_start_process(callback: types.CallbackQuery, callback_data: MenuCallbackData,
                                dialog_manager: DialogManager):
    await dialog_manager.start(state=CalendarSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


@dialogs_calendar_router.message(Command(commands='calendar'))
async def command_calendar_process(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=CalendarSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)
