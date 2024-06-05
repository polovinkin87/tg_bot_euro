from typing import Optional

from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_get_groups, orm_get_forecasts_by_two)
from kbds.inline import (
    get_user_main_btns, get_user_forecasts_btns, get_user_my_forecasts_btns, get_games_btns,
)
from utils.paginator import Paginator

image_id = 'AgACAgIAAxkBAAMJZj0EPhSkumlUjht4lBLLbMNqURYAApHcMRsEBelJ5f3hpmC0rnQBAAMCAAN5AAM1BA'
# image_id = 'AgACAgIAAxkBAANhZkXq0oL5SexKWFK8olhljU128YUAAizgMRtdzChKUjzXlpMJKfsBAAMCAAN5AAM1BA'


async def main_menu(level):
    image = InputMediaPhoto(media=image_id)
    kbds = get_user_main_btns(level=level)

    return image, kbds


async def forecasts_menu(level):
    image = InputMediaPhoto(media=image_id)
    kbds = get_user_forecasts_btns(level=level)

    return image, kbds


async def my_forecasts_menu(session, level):
    groups = await orm_get_groups(session)
    image = InputMediaPhoto(media=image_id, caption='Выбери группу 👇')
    kbds = get_user_my_forecasts_btns(level=level, groups=groups)

    return image, kbds


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns


async def forecasts_group_menu(session, level, group_id, page, user_id):
    games = await orm_get_forecasts_by_two(session, user_id=user_id, group_id=group_id)

    paginator = Paginator(games, page=page, per_page=3)
    games = paginator.get_page()

    image = InputMediaPhoto(media=image_id, caption='Выбери матч 👇')

    pagination_btns = pages(paginator)
    kbds = get_games_btns(level=level,
                          group_id=group_id,
                          page=page,
                          pagination_btns=pagination_btns,
                          games=games,
                          user_id=user_id)

    return image, kbds


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: Optional[str] = None,
        group_id: Optional[int] = None,
        page: Optional[int] = None,
        game_id: Optional[int] = None,
        user_id: Optional[int] = None,
):
    if level == 0:
        return await main_menu(level)
    elif level == 1 and menu_name == 'forecasts':
        return await forecasts_menu(level)
    elif level == 2 and menu_name == 'my_forecasts':
        return await my_forecasts_menu(session, level)
    elif level == 3:
        return await forecasts_group_menu(session, level, group_id, page, user_id)
