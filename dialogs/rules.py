from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode, ShowMode, Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format, Const

from handlers.menu_processing import main_menu
from kbds.inline import MenuCallbackData
from lexicon.lexicon import LEXICON

dialogs_rules_router = Router()


class RulesSG(StatesGroup):
    start = State()


async def rules_getter(dialog_manager: DialogManager, **kwargs):
    return {'rules': LEXICON['/rules']}


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await callback.message.delete()
    media, reply_markup = await main_menu(level=0)
    await callback.message.answer_photo(photo=media.media, reply_markup=reply_markup)
    await callback.answer()


rules_dialog = Dialog(
    Window(
        Format(text='{rules}'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked,
        ),
        getter=rules_getter,
        state=RulesSG.start,
    ),
)


# Это классический хэндлер на команду calendar
@dialogs_rules_router.callback_query(MenuCallbackData.filter(F.menu_name == 'rules'))
async def command_start_process(callback: types.CallbackQuery, callback_data: MenuCallbackData,
                                dialog_manager: DialogManager):
    await dialog_manager.start(state=RulesSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


@dialogs_rules_router.message(Command(commands='rules'))
async def command_rules_process(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=RulesSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)
