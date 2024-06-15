import datetime

from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window, ShowMode

from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_forecasts_for_table
from dialogs.state import MainSG, TableSG
from filters.chat_types import IsAdmin

dialogs_table_router = Router()


# dialogs_table_router.callback_query.filter(UserAuth())


async def table_getter(dialog_manager: DialogManager, session: AsyncSession, bot: Bot, **kwargs):
    table_str = await orm_get_forecasts_for_table(session)
    user_dict = {}
    for forecast in table_str:
        points = 0
        if forecast.game.goals_owner is not None and forecast.game.goals_guest is not None:
            if forecast.owner == forecast.game.goals_owner and forecast.guest == forecast.game.goals_guest:
                points += 3
            elif forecast.owner - forecast.guest == forecast.game.goals_owner - forecast.game.goals_guest:
                points += 2
            elif forecast.owner - forecast.guest == 0 and forecast.game.goals_owner - forecast.game.goals_guest == 0:
                points += 1
            elif forecast.owner - forecast.guest > 0 and forecast.game.goals_owner - forecast.game.goals_guest > 0:
                points += 1
            elif forecast.owner - forecast.guest < 0 and forecast.game.goals_owner - forecast.game.goals_guest < 0:
                points += 1

            if user_dict.get(forecast.user_id):
                start_points = user_dict.get(forecast.user_id)
                points += start_points[2]

            user_dict.update({forecast.user_id: [forecast.user.first_name, forecast.user.last_name, points]})

    user_list = [v for v in user_dict.values()]
    user_list = sorted(user_list, key=lambda x: x[2], reverse=True)
    user_list_new = []
    k = 1
    for i in user_list:
        i.append(k)
        user_list_new.append(i)
        k += 1

    user_str = '⚽️⚽️⚽️⚽️⚽️⚽️⚽️⚽️⚽⚽️⚽️⚽\n\nМесто | Участник | Кол-во очков\n\n'
    for v in user_list_new:
        user_str += f'{v[3]}. {v[0]} {v[1]} - <b>{v[2]}</b>\n'

    user_str += '\n⚽️⚽️⚽️⚽️⚽️⚽️⚽️⚽️⚽⚽️⚽️⚽'

    first_end_game = datetime.datetime.strptime('2024-06-15 00:00', '%Y-%m-%d %H:%M')
    left_before = first_end_game - datetime.datetime.now()

    if dialog_manager.event.from_user.id in bot.my_admins_list:
        is_admin = True
    else:
        is_admin = False

    return {'table': user_str, 'admin': is_admin, 'last_time': left_before}


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=MainSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


table_dialog = Dialog(
    Window(
        Format(text='{table}'),
        # Format(text='Здесь пока пусто. Таблица появится после первого сыгранного матча, а именно через:'
        #             '\n\n<b>{last_time}</b>'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_cancel',
            on_click=button_back_clicked,
        ),
        getter=table_getter,
        state=TableSG.start,
    ),
)


# Это классический хэндлер на команду table
@dialogs_table_router.message(Command(commands='table'))
async def command_table_process(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(state=TableSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)
