from aiogram import Router, types, F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode, ShowMode, Dialog, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Button, SwitchTo, Back, Group
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const

from dialogs.state import MainSG, ForecastsSG, CalendarSG, RulesSG, MyForecasts
from dialogs.statistics import TeamSG
from dialogs.table import TableSG

main_menu_router = Router()


async def get_photo(**kwargs):
    image_main_id = 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA'
    image_main = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_main_id))

    image_forecasts_id = 'AgACAgIAAxkBAAILzmZt5HlFVej5zIRoUrcyEZTuPXUZAAJU5DEbDs9hS_nWUPrKH2ZiAQADAgADeAADNQQ'
    image_forecasts = MediaAttachment(ContentType.PHOTO, file_id=MediaId(image_forecasts_id))
    return {'photo_main': image_main, 'photo_forecasts': image_forecasts}


async def button_clicked_all_forecasts(callback: CallbackQuery, widget: Button,
                                       dialog_manager: DialogManager):
    await dialog_manager.start(state=ForecastsSG.group, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def button_clicked_my_forecasts(callback: CallbackQuery, widget: Button,
                                      dialog_manager: DialogManager):
    await dialog_manager.start(state=MyForecasts.groups, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def button_clicked_table(callback: CallbackQuery, widget: Button,
                               dialog_manager: DialogManager):
    await dialog_manager.start(state=TableSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def button_clicked_calendar(callback: CallbackQuery, widget: Button,
                                  dialog_manager: DialogManager):
    await dialog_manager.start(state=CalendarSG.window_1, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def button_clicked_statistics(callback: CallbackQuery, widget: Button,
                                    dialog_manager: DialogManager):
    await dialog_manager.start(state=TeamSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


async def button_clicked_rules(callback: CallbackQuery, widget: Button,
                               dialog_manager: DialogManager):
    await dialog_manager.start(state=RulesSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


main_dialog = Dialog(
    Window(
        DynamicMedia('photo_main'),
        Group(
            SwitchTo(text=Const('Прогнозы 🎲'), id='forecasts', state=MainSG.forecasts),
            Button(text=Const('Турнирная таблица 📊'), id='table', on_click=button_clicked_table),
            Button(text=Const('Календарь 🗓'), id='calendar', on_click=button_clicked_calendar),
            Button(text=Const('Статистика 📌'), id='statistics', on_click=button_clicked_statistics),
            Button(text=Const('Правила ❗'), id='rules', on_click=button_clicked_rules),
            width=2
        ),
        state=MainSG.start,
        getter=get_photo
    ),
    Window(
        DynamicMedia('photo_forecasts'),
        Button(text=Const('Мои прогнозы 🎲'), id='my_forecasts', on_click=button_clicked_my_forecasts),
        Button(text=Const('Все прогнозы 🎯'), id='all_forecasts', on_click=button_clicked_all_forecasts),
        SwitchTo(text=Const('Назад ⬅️'), id='back', state=MainSG.start),
        state=MainSG.forecasts,
        getter=get_photo
    )
)


@main_menu_router.message(Command(commands='main'))
async def start_cmd(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=MainSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


@main_menu_router.message(Command(commands='forecasts'))
async def start_cmd(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=MainSG.forecasts, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


# @main_menu_router.message(F.photo)
# async def add_image(message: types.Message):
#     if message.photo:
#         await message.answer(message.photo[-1].file_id)
#     else:
#         await message.answer("Отправьте фото пищи")
