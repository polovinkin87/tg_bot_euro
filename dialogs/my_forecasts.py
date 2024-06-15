from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Select, Group, Button, Back, Next, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_groups, orm_get_forecasts_by_two
from dialogs.state import MyForecasts, MainSG, EditForecasts

my_forecasts_router = Router()


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


async def groups_selection(callback: CallbackQuery, widget: Select,
                           dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data.update({'group_id': int(item_id)})
    await dialog_manager.next()


async def get_groups(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_groups(session)
    groups_list = [(group.name, group.id) for group in data]

    image_id = 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA'
    image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_id))
    return {'groups': groups_list, 'photo': image}


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=MainSG.forecasts, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def go_to_forecasts(callback: CallbackQuery, widget: Select,
                          dialog_manager: DialogManager, item_id: str):
    await dialog_manager.start(state=EditForecasts.goals_owner, mode=StartMode.RESET_STACK,
                               data={'game_id': int(item_id)})


async def my_forecasts_getter_1(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_forecasts_by_two(session, user_id=dialog_manager.event.from_user.id,
                                          group_id=dialog_manager.dialog_data.get('group_id'))

    games = []
    for game in data[:3]:
        text = ''
        text += (f"{game.owner} - {game.guest} "
                 f"{'' if len(game.forecast) == 0 else game.forecast[0].owner}"
                 f"{'' if len(game.forecast) == 0 else ':'}"
                 f"{game.date_time.strftime('%d %B %H:%M') if len(game.forecast) == 0 else game.forecast[0].guest}")
        games.append([game.id, text])

    photo = await get_photo(dialog_manager.dialog_data.get('group_id'))
    return {'games': games, 'photo': photo}


async def my_forecasts_getter_2(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_forecasts_by_two(session, user_id=dialog_manager.event.from_user.id,
                                          group_id=dialog_manager.dialog_data.get('group_id'))

    games = []
    for game in data[3:]:
        text = ''
        text += (f"{game.owner} - {game.guest} "
                 f"{'' if len(game.forecast) == 0 else game.forecast[0].owner}"
                 f"{'' if len(game.forecast) == 0 else ':'}"
                 f"{game.date_time.strftime('%d %B %H:%M') if len(game.forecast) == 0 else game.forecast[0].guest}")
        games.append([game.id, text])

    photo = await get_photo(dialog_manager.dialog_data.get('group_id'))
    return {'games': games, 'photo': photo}


my_forecasts_dialog = Dialog(
    Window(
        DynamicMedia('photo'),
        Const(text='Выбери группу 👇'),
        Group(
            Select(
                Format('{item[0]}'),
                id='gr',
                item_id_getter=lambda x: x[1],
                items='groups',
                on_click=groups_selection,
            ),
            width=3
        ),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked,
        ),
        state=MyForecasts.groups,
        getter=get_groups,
    ),
    Window(
        Const(text='Выбери матч 👇'),
        DynamicMedia("photo"),
        Group(
            Select(
                Format('{item[1]}'),
                id='gm',
                item_id_getter=lambda x: x[0],
                items='games',
                on_click=go_to_forecasts,
            ),
            width=1
        ),
        Next(
            Const('Следующие ▶️'),
            id='b_next',
        ),
        Back(
            text=Const('Назад ⬅️'),
            id='button_back',
        ),
        getter=my_forecasts_getter_1,
        state=MyForecasts.games_1
    ),
    Window(
        Const(text='Выбери матч 👇'),
        DynamicMedia("photo"),
        Group(
            Select(
                Format('{item[1]}'),
                id='gm',
                item_id_getter=lambda x: x[0],
                items='games',
                on_click=go_to_forecasts,
            ),
            width=1
        ),
        Back(
            Const('Предыдущие ◀️'),
            id='b_next',
        ),
        SwitchTo(
            text=Const('Назад ⬅️'),
            id='button_back',
            state=MyForecasts.groups
        ),
        getter=my_forecasts_getter_2,
        state=MyForecasts.games_2
    ),
)
