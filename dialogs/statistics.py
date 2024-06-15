from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode, ShowMode, Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Group, Select
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_team_unique
from dialogs.state import MainSG, TeamSG
from lexicon.lexicon import LEXICON_APPLICATION

dialog_statistic_router = Router()


async def button_next(callback: CallbackQuery, widget: Button,
                      dialog_manager: DialogManager):
    await dialog_manager.next()


async def go_to_team(callback: CallbackQuery, widget: Select,
                     dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data.update({'team': item_id.split(' ')[-1]})
    await dialog_manager.switch_to(state=TeamSG.team_list, show_mode=ShowMode.EDIT)


async def go_back(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.back()


async def go_next(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


async def all_forecasts_getter_1(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_team_unique(session)
    team_list = [team for team in data]
    team_list = sorted(team_list, key=lambda x: x.split(' ')[-1])
    return {'teams': team_list[:12]}


async def all_forecasts_getter_2(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_team_unique(session)
    team_list = [team for team in data]
    team_list = sorted(team_list, key=lambda x: x.split(' ')[-1])
    return {'teams': team_list[12:]}


async def all_forecasts_getter_3(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    team = LEXICON_APPLICATION[dialog_manager.dialog_data.get('team')]
    return {'team': team}


async def button_back_clicked_2(callback: CallbackQuery, widget: Button,
                                dialog_manager: DialogManager):
    await dialog_manager.start(state=TeamSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def button_back_clicked_3(callback: CallbackQuery, widget: Button,
                                dialog_manager: DialogManager):
    await dialog_manager.back()


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=MainSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


team_dialog = Dialog(
    Window(
        Const('Выбери статистику'),
        Button(
            text=Const('Составы'),
            id='button_next',
            on_click=button_next,
        ),
        Button(
            text=Const('Назад ⬅️'),
            id='button_cancel',
            on_click=button_back_clicked,
        ),
        state=TeamSG.start,
    ),
    Window(
        Const(text='Выбери команду:'),
        # DynamicMedia("photo"),
        Group(
            Select(
                Format('{item}'),
                id='team',
                item_id_getter=lambda x: x,
                items='teams',
                on_click=go_to_team,
            ),
            width=3
        ),
        Button(
            Const('Следующие ▶️'),
            id='b_next',
            on_click=go_next),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked_2,
        ),
        getter=all_forecasts_getter_1,
        state=TeamSG.team_1
    ),
    Window(
        Const(text='Выбери команду:'),
        # DynamicMedia("photo"),
        Group(
            Select(
                Format('{item}'),
                id='team',
                item_id_getter=lambda x: x,
                items='teams',
                on_click=go_to_team,
            ),
            width=3
        ),
        Button(
            Const('Предыдущие ◀️'),
            id='b_back',
            on_click=go_back),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked_2,
        ),
        getter=all_forecasts_getter_2,
        state=TeamSG.team_2
    ),
    Window(
        Format('{team}'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked_3,
        ),
        getter=all_forecasts_getter_3,
        state=TeamSG.team_list
    ),
)
