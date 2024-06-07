import datetime

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, contains_eager, aliased

from database.models import Group, Game, Forecast, User


############################ Группы ######################################

async def orm_get_groups(session: AsyncSession):
    query = select(Group)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_add_group(session: AsyncSession, name: str):
    query = select(Group).where(Group.name == name)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            Group(name=name)
        )
        await session.commit()
        return True
    else:
        await session.commit()
        return False


############ Админка: добавить/изменить матч ########################

async def orm_add_game(session: AsyncSession, data: dict):
    obj = Game(
        owner=data["owner"],
        guest=data["guest"],
        goals_owner=data["goals_owner"],
        goals_guest=data["goals_guest"],
        date_time=datetime.datetime.strptime(data["date_time"], '%Y-%m-%d %H:%M'),
        group_id=int(data["group"]),
    )
    session.add(obj)
    await session.commit()


async def orm_get_games(session: AsyncSession, group_id):
    query = select(Game).where(Game.group_id == int(group_id)).order_by(Game.date_time)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_game(session: AsyncSession, game_id: int):
    query = select(Game).where(Game.id == game_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_game(session: AsyncSession, game_id: int, data):
    query = (
        update(Game)
        .where(Game.id == game_id)
        .values(
            owner=data["owner"],
            guest=data["guest"],
            goals_owner=int(data["goals_owner"]),
            goals_guest=int(data["goals_guest"]),
            date_time=datetime.datetime.strptime(data["date_time"], '%Y-%m-%d %H:%M'),
            group_id=int(data["group"]),
        )
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_game(session: AsyncSession, game_id: int):
    query = delete(Game).where(Game.id == game_id)
    await session.execute(query)
    await session.commit()


##################### Добавляем юзера в БД #####################################

async def orm_get_user(session: AsyncSession):
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_check_user(session: AsyncSession, user_id: int):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_add_user(session: AsyncSession, data):
    session.add(
        User(user_id=data['user_id'], first_name=data['first_name'], last_name=data['last_name'], phone=data['phone'])
    )
    await session.commit()


######################## Работа с прогнозами #######################################

async def orm_add_forecast(session: AsyncSession, user_id: int, game_id: int, owner: int, guest: int):
    session.add(Forecast(user_id=user_id, game_id=game_id, owner=owner, guest=guest))
    await session.commit()


async def orm_get_forecasts_for_table(session: AsyncSession):
    query = select(Forecast).options(joinedload(Forecast.user)).options(joinedload(Forecast.game))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_forecasts(session: AsyncSession, user_id: int, game_id: int):
    query = select(Forecast).filter(Forecast.user_id == user_id, Forecast.game_id == game_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_all_forecasts(session: AsyncSession, game_id: int):
    query = select(Forecast).filter(Forecast.game_id == game_id).options(joinedload(Forecast.user)).options(
        joinedload(Forecast.game))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_forecasts_by_two(session: AsyncSession, user_id: int, group_id: int):
    subquery = select(Forecast).join(User).filter(User.user_id == user_id).subquery()
    alias = aliased(Forecast, subquery)

    query = select(Game).outerjoin(Game.forecast.of_type(alias), ).filter(Game.group_id == group_id).options(
        contains_eager(Game.forecast.of_type(alias)), ).order_by(Game.date_time)

    result = await session.execute(query)
    return result.unique().scalars().all()


async def orm_update_forecast(session: AsyncSession, forecast_id: int, owner: int, guest: int):
    query = (
        update(Forecast)
        .where(Forecast.id == forecast_id)
        .values(
            owner=owner,
            guest=guest,
        )
    )
    await session.execute(query)
    await session.commit()
