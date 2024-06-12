from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode, ShowMode, Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Next, Back
from aiogram_dialog.widgets.text import Format, Const
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_forecasts_for_calendar
from handlers.menu_processing import main_menu
from kbds.inline import MenuCallbackData

dialogs_calendar_router = Router()


class CalendarSG(StatesGroup):
    window_1 = State()
    window_2 = State()
    window_3 = State()
    window_4 = State()


async def all_forecasts_getter_1(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data: list = await orm_get_forecasts_for_calendar(session, dialog_manager.event.from_user.id)
    dialog_manager.dialog_data.update({'len_data': len(data)})
    text = ''
    for game in data[:13]:
        text += (f"{game.owner} - {game.guest} <b>{game.forecast[0].owner if game.forecast else ''}"
                 f"{':' if game.forecast else ''}"
                 f"{game.forecast[0].guest if game.forecast else game.date_time.strftime('%d %B %H:%M')}</b>\n")

    return {'games': text}


async def all_forecasts_getter_2(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_forecasts_for_calendar(session, dialog_manager.event.from_user.id)
    len_data = dialog_manager.dialog_data.get('len_data')
    text = ''
    for game in data[13:26]:
        text += (f"{game.owner} - {game.guest} <b>{game.forecast[0].owner if game.forecast else ''}"
                 f"{':' if game.forecast else ''}"
                 f"{game.forecast[0].guest if game.forecast else game.date_time.strftime('%d %B %H:%M')}</b>\n")

    if len_data > 26:
        button_clicked = True
    else:
        button_clicked = False

    return {'games': text, 'len_data': button_clicked}


async def all_forecasts_getter_3(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_forecasts_for_calendar(session, dialog_manager.event.from_user.id)
    len_data = dialog_manager.dialog_data.get('len_data')
    text = ''
    for game in data[26:39]:
        text += (f"{game.owner} - {game.guest} <b>{game.forecast[0].owner if game.forecast else ''}"
                 f"{':' if game.forecast else ''}"
                 f"{game.forecast[0].guest if game.forecast else game.date_time.strftime('%d %B %H:%M')}</b>\n")

    if len_data > 39:
        button_clicked = True
    else:
        button_clicked = False

    return {'games': text, 'len_data': button_clicked}


async def all_forecasts_getter_4(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    data = await orm_get_forecasts_for_calendar(session, dialog_manager.event.from_user.id)
    text = ''
    for game in data[39:]:
        text += (f"{game.owner} - {game.guest} <b>{game.forecast[0].owner if game.forecast else ''}"
                 f"{':' if game.forecast else ''}"
                 f"{game.forecast[0].guest if game.forecast else game.date_time.strftime('%d %B %H:%M')}<b>\n")

    return {'games': text}


async def button_back_clicked(callback: CallbackQuery, widget: Button,
                              dialog_manager: DialogManager):
    await dialog_manager.done()
    await callback.message.delete()
    media, reply_markup = await main_menu(level=0)
    await callback.message.answer_photo(photo=media.media, reply_markup=reply_markup)
    await callback.answer()


# calendar_dialog = Dialog(
#     Window(
#         Const(text='Админ вчера выпил много пенного 🍻 - данная опция пока недоступна.'),
#         Button(
#             text=Const('Назад ⬅️'),
#             id='button_back',
#             on_click=button_back_clicked,
#         ),
#         state=CalendarSG.start,
#     ),
# )

calendar_dialog = Dialog(
    Window(
        Format(text='{games}'
               ),
        Next(Const('Следующие ▶️'), id='b_next'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked,
        ),
        getter=all_forecasts_getter_1,
        state=CalendarSG.window_1
    ),
    Window(
        Format(text='{games}'
               ),
        Next(Const('Следующие ▶️'), id='b_next', when='len_data'),
        Back(Const('Предыдущие ◀️'), id='b_back'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked,
        ),
        getter=all_forecasts_getter_2,
        state=CalendarSG.window_2
    ),
    Window(
        Format(text='{games}'
               ),
        Next(Const('Следующие ▶️'), id='b_next', when='len_data'),
        Back(Const('Предыдущие ◀️'), id='b_back'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked,
        ),
        getter=all_forecasts_getter_3,
        state=CalendarSG.window_3
    ),
    Window(
        Format(text='{games}'
               ),
        Back(Const('Предыдущие ◀️'), id='b_back'),
        Button(
            text=Const('Назад ⬅️'),
            id='button_back',
            on_click=button_back_clicked,
        ),
        getter=all_forecasts_getter_4,
        state=CalendarSG.window_4
    ),
)


# Это классический хэндлер на команду calendar
@dialogs_calendar_router.callback_query(MenuCallbackData.filter(F.menu_name == 'calendar'))
async def command_start_process(callback: types.CallbackQuery, callback_data: MenuCallbackData,
                                dialog_manager: DialogManager):
    await dialog_manager.start(state=CalendarSG.window_1, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)


@dialogs_calendar_router.message(Command(commands='calendar'))
async def command_calendar_process(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=CalendarSG.window_1, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT)
