import datetime

from aiogram import Router, types, F, Bot
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window, StartMode, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Select, Group, Button
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_groups, orm_get_games, orm_get_all_forecasts
from handlers.menu_processing import forecasts_menu, get_menu_content
from kbds.inline import MenuCallbackData

dialog_forecast_router = Router()


class StartSG(StatesGroup):
    group = State()


class SecondSG(StatesGroup):
    window_1 = State()
    window_2 = State()
    forecasts = State()


# Это хэндлер, срабатывающий на нажатие кнопки с группой
async def groups_selection(callback: CallbackQuery, widget: Select,
                           dialog_manager: DialogManager, item_id: str):
    await dialog_manager.start(state=SecondSG.window_1, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT,
                               data={'group_id': int(item_id)})


# Это геттер
async def get_groups(dialog_manager: DialogManager, bot: Bot, session: AsyncSession, **kwargs):
    data = await orm_get_groups(session)
    groups_list = [(group.name, group.id) for group in data]
    return {'groups': groups_list}


async def button_back_clicked_1(callback: CallbackQuery, widget: Button,
                                dialog_manager: DialogManager):
    await dialog_manager.done()
    await callback.message.delete()
    media, reply_markup = await forecasts_menu(level=1)
    await callback.message.answer_photo(photo=media.media, reply_markup=reply_markup)
    await callback.answer()


forecast_start_dialog = Dialog(
    Window(
        Const(text='Выберите группу:'),
        # DynamicMedia("photo"),
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
                id='button_back',
                on_click=button_back_clicked_1,
            ),
            width=3
        ),
        state=StartSG.group,
        getter=get_groups,
    ),
)


async def go_to_forecasts(callback: CallbackQuery, widget: Select,
                          dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data.update({'game_id': int(item_id)})
    await dialog_manager.switch_to(state=SecondSG.forecasts, show_mode=ShowMode.EDIT)


async def go_back(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.back()


async def go_next(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


async def all_forecasts_getter_1(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_games(session, dialog_manager.start_data['group_id'])
    games_list = [(game.owner, game.guest, game.id) for game in data]
    return {'games': games_list[:3]}


async def all_forecasts_getter_2(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_games(session, dialog_manager.start_data['group_id'])
    games_list = [(game.owner, game.guest, game.id) for game in data]
    return {'games': games_list[3:]}


async def all_forecasts_getter_3(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_all_forecasts(session, dialog_manager.dialog_data.get('game_id'))
    forecasts_str = ''
    for forecasts in data:
        forecasts_str += (f'{forecasts.user.first_name} {forecasts.user.last_name} '
                          f'{forecasts.owner}:{forecasts.guest}\n')

    if datetime.datetime.now() < data[0].game.date_time:
        forecasts_str = '❌ Информация появится после начала матча ❌'

    # image_id = "AgACAgIAAxkBAANhZkXq0oL5SexKWFK8olhljU128YUAAizgMRtdzChKUjzXlpMJKfsBAAMCAAN5AAM1BA"
    # image = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_id))

    return {'forecasts': forecasts_str}


async def button_back_clicked_2(callback: CallbackQuery, widget: Button,
                                dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.group, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def button_back_clicked_3(callback: CallbackQuery, widget: Button,
                                dialog_manager: DialogManager):
    await dialog_manager.start(state=SecondSG.window_1, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT,
                               data={'group_id': dialog_manager.start_data['group_id']})


forecast_second_dialog = Dialog(
    Window(
        Const(text='Выберите матч:'),
        # DynamicMedia("photo"),
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
        state=SecondSG.window_1
    ),
    Window(
        Const(text='Выберите матч:'),
        # DynamicMedia("photo"),
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
        state=SecondSG.window_2
    ),
    Window(
        Format('{forecasts}'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked_3,
        ),
        getter=all_forecasts_getter_3,
        state=SecondSG.forecasts
    ),
)


@dialog_forecast_router.callback_query(MenuCallbackData.filter(F.menu_name == 'all_forecasts'))
async def all_forecasts_process(callback: types.CallbackQuery, callback_data: MenuCallbackData,
                                dialog_manager: DialogManager, session: AsyncSession):
    await dialog_manager.start(state=StartSG.group, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


@dialog_forecast_router.message(Command(commands='forecasts'))
async def forecasts_process(message: types.Message, dialog_manager: DialogManager, session: AsyncSession):
    try:
        await dialog_manager.done()
        await message.delete_reply_markup()
    except Exception as err:
        print(err)
    media, reply_markup = await get_menu_content(session, level=1, menu_name=message.text[1:])
    await message.answer_photo(photo=media.media, reply_markup=reply_markup)
