from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode, ShowMode, Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format, Const

from dialogs.state import RulesSG, MainSG
from lexicon.lexicon import LEXICON

dialogs_rules_router = Router()


async def rules_getter(dialog_manager: DialogManager, **kwargs):
    return {'rules': LEXICON['/rules']}


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=MainSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


rules_dialog = Dialog(
    Window(
        Format(text='{rules}'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_cancel',
            on_click=button_back_clicked,
        ),
        getter=rules_getter,
        state=RulesSG.start,
    ),
)
