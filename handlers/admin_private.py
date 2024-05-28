import datetime
import re
import locale

from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_get_groups,
    orm_add_game,
    orm_get_game,
    orm_get_games,
    orm_update_game, orm_add_group, orm_delete_game,
)

from filters.chat_types import ChatTypeFilter, IsAdmin

from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())
# locale.setlocale(locale.LC_ALL, ('ru_RU', 'UTF-8'))

ADMIN_KB = get_keyboard(
    "Добавить группу/стадию плэй-офф",
    "Добавить матч",
    "Календарь",
    placeholder="Выберите действие",
    sizes=(1,)
)


@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


class AddGroup(StatesGroup):
    group = State()


# Становимся в состояние ожидания ввода group
@admin_router.message(StateFilter(None), F.text == 'Добавить группу/стадию плэй-офф')
async def add_group(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название группы/стадии плэй-офф", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddGroup.group)


@admin_router.message(AddGroup.group, F.text)
async def add_group2(message: types.Message, state: FSMContext, session: AsyncSession):
    if await orm_add_group(session, message.text):
        await message.answer('Группа/стадия добавлена', reply_markup=ADMIN_KB)
    else:
        await message.answer('Такая группа/стадия уже есть', reply_markup=ADMIN_KB)
    await state.clear()


# Хендлер для отлова некорректных вводов для состояния group
@admin_router.message(AddGroup.group)
async def add_group3(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст названия группы/стадии")


@admin_router.message(F.text == 'Календарь')
async def all_games(message: types.Message, session: AsyncSession):
    groups = await orm_get_groups(session)
    btns = {group.name: f'group_{group.id}' for group in groups}
    await message.answer("Выберите группу/стадию", reply_markup=get_callback_btns(btns=btns))


@admin_router.callback_query(F.data.startswith('group_'))
async def starring_at_group(callback: types.CallbackQuery, session: AsyncSession):
    group_id = callback.data.split('_')[-1]
    for game in await orm_get_games(session, int(group_id)):
        await callback.message.answer(
            f"{game.owner} - {game.guest} <strong>{'' if game.goals_owner is None else game.goals_owner}"
            f"{'' if game.goals_owner is None else ':'}"
            f"{'' if game.goals_guest is None else game.goals_guest}</strong>"
            f"\n{game.date_time.strftime('%d %B %H:%M')}",
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"delete_{game.id}",
                    "Изменить": f"change_{game.id}",
                },
                sizes=(2,)
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список матчей ⏫")


@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_game_callback(callback: types.CallbackQuery, session: AsyncSession):
    game_id = callback.data.split("_")[-1]
    await orm_delete_game(session, int(game_id))

    await callback.answer("Матч удален")
    await callback.message.answer("Матч удален!")


######################### FSM для дабавления/изменения матчей админом ###################

class AddGame(StatesGroup):
    # Шаги состояний
    owner = State()
    guest = State()
    goals_owner = State()
    goals_guest = State()
    date_time = State()
    group = State()

    game_for_change = None

    texts = {
        "AddGame:owner": "Введите название команды хозяев заново:",
        "AddGame:guest": "Введите название команды гостей заново:",
        "AddGame:goals_owner": "Введите количество голов хозяев заново",
        "AddGame:goals_guest": "Введите количество голов гостей заново:",
        "AddGame:date_time": "Введите дату и время проведения матча заново:",
        "AddGame:group": "Этот стейт последний, поэтому...",
    }


# Становимся в состояние ожидания ввода owner
@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_game_callback(
        callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    game_id = callback.data.split("_")[-1]

    game_for_change = await orm_get_game(session, int(game_id))

    AddGame.game_for_change = game_for_change

    await callback.answer()
    await callback.message.answer(
        "Введите название команды хозяев", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddGame.owner)


# Становимся в состояние ожидания ввода owner
@admin_router.message(StateFilter(None), F.text == "Добавить матч")
async def add_game(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название команды хозяев", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddGame.owner)


# Хендлер отмены и сброса состояния должен быть всегда именно здесь,
# после того, как только встали в состояние номер 1 (элементарная очередность фильтров)
@admin_router.message(StateFilter("*"), Command("отмена"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddGame.game_for_change:
        AddGame.game_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


# Вернутся на шаг назад (на прошлое состояние)
@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddGame.owner:
        await message.answer(
            'Предыдущего шага нет, или введите название команды или напишите "отмена"'
        )
        return

    previous = None
    for step in AddGame.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу.\n{AddGame.texts[previous.state]}"
            )
            return
        previous = step


# Ловим данные для состояния owner и потом меняем состояние на guest
@admin_router.message(AddGame.owner, F.text)
async def add_owner(message: types.Message, state: FSMContext):
    if message.text == "." and AddGame.game_for_change:
        await state.update_data(owner=AddGame.game_for_change.owner)
    else:
        # Здесь можно сделать какую либо дополнительную проверку
        # и выйти из хендлера не меняя состояние с отправкой соответствующего сообщения
        # например:
        if 4 >= len(message.text) >= 150:
            await message.answer(
                "Название команды не должно превышать 150 символов\nили быть менее 5ти символов."
                "\n Введите заново"
            )
            return

        await state.update_data(owner=message.text)
    await message.answer("Введите название команды гостей")
    await state.set_state(AddGame.guest)


# Хендлер для отлова некорректных вводов для состояния owner
@admin_router.message(AddGame.owner)
async def add_owner2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст названия команды хозяев")


# Ловим данные для состояния guest и потом меняем состояние на goals_owner
@admin_router.message(AddGame.guest, F.text)
async def add_guest(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == "." and AddGame.game_for_change:
        await state.update_data(guest=AddGame.game_for_change.guest)
    else:
        if 4 >= len(message.text) >= 150:
            await message.answer(
                "Название команды не должно превышать 150 символов\nили быть менее 5ти символов."
                "\n Введите заново"
            )
            return
        await state.update_data(guest=message.text)

    await message.answer("Введите количество голов хозяев")
    await state.set_state(AddGame.goals_owner)


# Хендлер для отлова некорректных вводов для состояния guest
@admin_router.message(AddGame.guest)
async def add_guest2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст названия команды гостей")


# Ловим данные для состояние goals_owner и потом меняем состояние на goals_guest
@admin_router.message(AddGame.goals_owner, F.text)
async def add_goals_owner(message: types.Message, state: FSMContext):
    if message.text == "." and AddGame.game_for_change:
        await state.update_data(goals_owner=AddGame.game_for_change.goals_owner)
    elif message.text == ".":
        await state.update_data(goals_owner=None)
    else:
        try:
            int(message.text)
        except ValueError:
            await message.answer("Введите корректное количество голов хозяев")
            return

        await state.update_data(goals_owner=message.text)
    await message.answer("Введите количество голов гостей")
    await state.set_state(AddGame.goals_guest)


# Хендлер для отлова некорректного ввода для состояния goals_owner
@admin_router.message(AddGame.goals_owner)
async def add_goals_owner2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите корректное количество голов хозяев")


# Ловим данные для состояния goals_guest и потом меняем состояние на group
@admin_router.message(AddGame.goals_guest, F.text)
async def add_goals_guest(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == "." and AddGame.game_for_change:
        await state.update_data(goals_guest=AddGame.game_for_change.goals_guest)
    elif message.text == ".":
        await state.update_data(goals_guest=None)
    else:
        try:
            int(message.text)
        except ValueError:
            await message.answer("Введите корректное количество голов гостей")
            return

        await state.update_data(goals_guest=message.text)
    groups = await orm_get_groups(session)
    btns = {group.name: str(group.id) for group in groups}
    await message.answer("Выберите группу", reply_markup=get_callback_btns(btns=btns))
    await state.set_state(AddGame.group)


# Хендлер для отлова некорректного ввода для состояния goals_guest
@admin_router.message(AddGame.goals_guest)
async def add_goals_guest2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите корректное количество голов гостей")


# Ловим callback выбора группы
@admin_router.callback_query(AddGame.group)
async def group_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    if int(callback.data) in [group.id for group in await orm_get_groups(session)]:
        await callback.answer()
        await state.update_data(group=callback.data)
        await callback.message.answer("Теперь введите дату и время проведения матча в формате 'ГГГГ-ММ-ДД ЧЧ:ММ'")
        await state.set_state(AddGame.date_time)
    else:
        await callback.message.answer('Выберите группу нажатием на кнопку.')
        await callback.answer()


# Ловим любые некорректные действия, кроме нажатия на кнопку выбора группы
@admin_router.message(AddGame.group)
async def group_choice2(message: types.Message, state: FSMContext):
    await message.answer('Выберите группу из кнопок')


# Ловим данные для состояния date_time и потом выходим из состояний
@admin_router.message(AddGame.date_time, F.text)
async def add_date_time(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == "." and AddGame.game_for_change:
        await state.update_data(date_time=AddGame.game_for_change.date_time)
    else:
        try:
            re.fullmatch(r'\d{4}.\d{2}.\d{2} \d{2}:\d{2}', message.text)
        except ValueError:
            await message.answer("Введите корректные дату и время проведения матча")
            return
        await state.update_data(date_time=datetime.datetime.strptime(message.text, '%Y-%m-%d %H:%M'))
    data = await state.get_data()
    try:
        if AddGame.game_for_change:
            await orm_update_game(session, AddGame.game_for_change.id, data)
        else:
            await orm_add_game(session, data)
        await message.answer("Матч добавлен/изменен", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к программеру, он опять денег хочет",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    AddGame.game_for_change = None


# Ловим все прочее некорректное поведение для этого состояния
@admin_router.message(AddGame.date_time)
async def add_date_time2(message: types.Message, state: FSMContext):
    await message.answer("Введите корректные дату и время проведения матча")
