import datetime

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Select, Group, Button, Back, Next, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_groups, orm_get_forecasts_by_two, orm_get_game
from dialogs.state import MyForecasts, MainSG, EditForecasts

my_forecasts_router = Router()


async def get_photo(group_id):
    images = {
        1: 'AgACAgIAAxkBAAIL0GZt5QpMLqJgQrrGNBw-ZBCi6F78AAIc2zEb0a1wSw-yA3WmjlSZAQADAgADeAADNQQ',
        2: 'AgACAgIAAxkBAAIL0mZt5XmC2AogRbwgrJNvyDq2A8fCAAIe2zEb0a1wSzQlzl4HdXs9AQADAgADeAADNQQ',
        3: 'AgACAgIAAxkBAAIL1GZt5a5ITYrtglgMHQO6hWHpZBTSAAIi2zEb0a1wS-w4WFByD90rAQADAgADeAADNQQ',
        4: 'AgACAgIAAxkBAAIL1mZt5eFeOZQCGg0tbw-qbXz1FEHPAAIj2zEb0a1wS-hvTyH0gBdqAQADAgADeAADNQQ',
        5: 'AgACAgIAAxkBAAIL2GZt5kZfLWrjunPMBsQViVwz1q90AAIk2zEb0a1wSwTRETTo4gnMAQADAgADeAADNQQ',
        6: 'AgACAgIAAxkBAAIL2mZt5rEg3lVAIPaNkMQOeHNZsAcRAAI12zEb0a1wSyM-m5QekbTYAQADAgADeAADNQQ',
        7: 'AgACAgIAAxkBAAIYTGZ8I6wq9pW0Wy9Imq16tjhD5G_hAAI32jEb39LgS3ulwx162k-VAQADAgADeAADNQQ',
        8: 'AgACAgIAAxkBAAIc4GaECA2cD23Gri6fQqlGnT93tJ5GAAKe2jEbVJwhSD4Vw7fbt-OkAQADAgADeAADNQQ',
        9: 'AgACAgIAAxkBAAIfJWaMAzBSgooocz7sA2xOwb6FNYvhAAJx3DEbKwJhSF6gG8HCpKFWAQADAgADeAADNQQ',
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

    image_id = 'AgACAgIAAxkBAAIL3GZt5x9suaIqIM6y9qFnk9IkraXzAAKz2jEb0a1wSwVDJu1HSpPOAQADAgADeAADNQQ'
    image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_id))
    return {'groups': groups_list, 'photo': image}


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=MainSG.forecasts, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def go_to_forecasts(callback: CallbackQuery, widget: Select,
                          dialog_manager: DialogManager, item_id: str):
    game = await orm_get_game(dialog_manager.middleware_data.get('session'), int(item_id))
    if datetime.datetime.now() + datetime.timedelta(hours=4) < game.date_time:
        await dialog_manager.start(state=EditForecasts.goals_owner, mode=StartMode.RESET_STACK,
                                   data={'game_id': int(item_id)})
    else:
        await callback.answer(text='Ты не успел сделать ставку!', show_alert=True)


async def my_forecasts_getter_1(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_forecasts_by_two(session, user_id=dialog_manager.event.from_user.id,
                                          group_id=dialog_manager.dialog_data.get('group_id'))

    games = []
    for game in data[:4]:
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
    for game in data[4:]:
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
        Const(text='Выбери группу 👇'),
        DynamicMedia('photo'),
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
