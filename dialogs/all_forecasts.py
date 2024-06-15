import datetime

from aiogram import Router, types, F, Bot
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window, StartMode, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Select, Group, Button, Cancel
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_groups, orm_get_games, orm_get_all_forecasts
from dialogs.state import MainSG, ForecastsSecondSG, ForecastsSG
from handlers.menu_processing import forecasts_menu, get_menu_content

dialog_forecast_router = Router()


async def get_photo(group_id):
    images = {
        1: 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA',
        2: 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA',
        3: 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA',
        4: 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA',
        5: 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA',
        6: 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA',
    }
    image_forecasts = MediaAttachment(ContentType.PHOTO, file_id=MediaId(images[group_id]))
    return image_forecasts


# Это хэндлер, срабатывающий на нажатие кнопки с группой
async def groups_selection(callback: CallbackQuery, widget: Select,
                           dialog_manager: DialogManager, item_id: str):
    await dialog_manager.start(state=ForecastsSecondSG.window_1, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT,
                               data={'group_id': int(item_id)})


# Это геттер
async def get_groups(dialog_manager: DialogManager, bot: Bot, session: AsyncSession, **kwargs):
    data = await orm_get_groups(session)
    groups_list = [(group.name, group.id) for group in data]

    image_id = 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA'
    image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_id))
    return {'groups': groups_list, 'photo': image}


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=MainSG.forecasts, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


forecast_start_dialog = Dialog(
    Window(
        Const(text='Выбери группу 👇'),
        DynamicMedia("photo"),
        Group(
            Select(
                Format('{item[0]}'),
                id='gr',
                item_id_getter=lambda x: x[1],
                items='groups',
                on_click=groups_selection,
            ),
            Button(
                text=Const('Назад ⬅️'),
                id='button_cancel',
                on_click=button_back_clicked
            ),
            width=3
        ),
        state=ForecastsSG.group,
        getter=get_groups,
    ),
)


async def go_to_forecasts(callback: CallbackQuery, widget: Select,
                          dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data.update({'game_id': int(item_id)})
    await dialog_manager.switch_to(state=ForecastsSecondSG.forecasts, show_mode=ShowMode.EDIT)


async def go_back(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.back()


async def go_next(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


async def all_forecasts_getter_1(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_games(session, dialog_manager.start_data['group_id'])
    games_list = [(game.owner, game.guest, game.id) for game in data]

    photo = await get_photo(dialog_manager.start_data.get('group_id'))
    return {'games': games_list[:3], 'photo': photo}


async def all_forecasts_getter_2(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_games(session, dialog_manager.start_data['group_id'])
    games_list = [(game.owner, game.guest, game.id) for game in data]

    photo = await get_photo(dialog_manager.start_data.get('group_id'))
    return {'games': games_list[3:], 'photo': photo}


async def all_forecasts_getter_3(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_all_forecasts(session, dialog_manager.dialog_data.get('game_id'))
    forecasts_str = ''
    for forecasts in data:
        forecasts_str += (f'{forecasts.user.first_name} {forecasts.user.last_name} '
                          f'{forecasts.owner}:{forecasts.guest}\n')

    if len(data) > 0:
        if datetime.datetime.now() + datetime.timedelta(hours=3) < data[0].game.date_time:
            forecasts_str = '❌ Информация появится после начала матча ❌'
    else:
        forecasts_str = '❌ Здесь пока нет ни одного прогноза ❌'

    return {'forecasts': forecasts_str}


async def button_back_clicked_2(callback: CallbackQuery, widget: Button,
                                dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=ForecastsSG.group, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def button_back_clicked_3(callback: CallbackQuery, widget: Button,
                                dialog_manager: DialogManager):
    await dialog_manager.start(state=ForecastsSecondSG.window_1, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT,
                               data={'group_id': dialog_manager.start_data['group_id']})


forecast_second_dialog = Dialog(
    Window(
        Const(text='Выбери матч 👇'),
        DynamicMedia("photo"),
        Group(
            Select(
                Format('{item[0]} - {item[1]}'),
                id='gm',
                item_id_getter=lambda x: x[2],
                items='games',
                on_click=go_to_forecasts,
            ),
            width=1
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
        state=ForecastsSecondSG.window_1
    ),
    Window(
        Const(text='Выбери матч 👇'),
        DynamicMedia("photo"),
        Group(
            Select(
                Format('{item[0]} - {item[1]}'),
                id='gm',
                item_id_getter=lambda x: x[2],
                items='games',
                on_click=go_to_forecasts,
            ),
            width=1
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
        state=ForecastsSecondSG.window_2
    ),
    Window(
        Format('{forecasts}'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked_3,
        ),
        getter=all_forecasts_getter_3,
        state=ForecastsSecondSG.forecasts
    ),
)
