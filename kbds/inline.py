from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuCallbackData(CallbackData, prefix="menu"):
    level: int
    menu_name: Optional[str] = None
    group_id: Optional[int] = None
    page: Optional[int] = 1
    game_id: Optional[int] = None
    user_id: Optional[int] = None


def get_user_main_btns(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Прогнозы 🎲": "forecasts",
        "Турнирная таблица 📊": "table",
        "Календарь 🗓️": "calendar",
        "Статистика 📌": "statistics",
        "Правила ❗️": "rules",
    }
    for text, menu_name in btns.items():
        keyboard.add(InlineKeyboardButton(text=text,
                                          callback_data=MenuCallbackData(level=level + 1, menu_name=menu_name).pack()))
    return keyboard.adjust(*sizes).as_markup()


def get_user_forecasts_btns(*, level: int, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Мои прогнозы 🎲": "my_forecasts",
        "Все прогнозы 🎯": "all_forecasts",
    }
    for text, menu_name in btns.items():
        keyboard.add(InlineKeyboardButton(text=text,
                                          callback_data=MenuCallbackData(level=level + 1, menu_name=menu_name).pack()))
    keyboard.add(
        InlineKeyboardButton(text='Назад ⬅️', callback_data=MenuCallbackData(level=level - 1, menu_name='main').pack()))
    return keyboard.adjust(*sizes).as_markup()


def get_user_my_forecasts_btns(*, level: int, groups: list, sizes: tuple[int] = (4,)):
    keyboard = InlineKeyboardBuilder()
    for g in groups:
        keyboard.add(InlineKeyboardButton(text=g.name,
                                          callback_data=MenuCallbackData(level=level + 1, menu_name=g.name,
                                                                         group_id=g.id).pack()))
    keyboard.add(
        InlineKeyboardButton(text='Назад ⬅️',
                             callback_data=MenuCallbackData(level=level - 1, menu_name='forecasts').pack()))
    return keyboard.adjust(*sizes).as_markup()


def get_games_btns(*, level: int, group_id: int, page: int, pagination_btns: dict, games: list, user_id: int, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    for game in games:
        keyboard.add(InlineKeyboardButton(
            text=f"{game.owner} - {game.guest} "
                 f"{'' if len(game.forecast) == 0 else game.forecast[0].owner}"
                 f"{'' if len(game.forecast) == 0 else ':'}"
                 f"{game.date_time.strftime('%d %B %H:%M') if len(game.forecast) == 0 else game.forecast[0].guest}",
            callback_data=MenuCallbackData(level=level, game_id=game.id, user_id=user_id).pack()))

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallbackData(
                                                level=level,
                                                menu_name=menu_name,
                                                group_id=group_id,
                                                page=page + 1).pack()))

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallbackData(
                                                level=level,
                                                menu_name=menu_name,
                                                group_id=group_id,
                                                page=page - 1).pack()))

    keyboard.row(*row)
    keyboard.add(
        InlineKeyboardButton(text='Назад ⬅️',
                             callback_data=MenuCallbackData(level=level - 1, menu_name='my_forecasts').pack()))
    return keyboard.adjust(*sizes).as_markup()


def get_callback_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
