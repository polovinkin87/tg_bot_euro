from aiogram.fsm.state import StatesGroup, State


class MainSG(StatesGroup):
    start = State()
    forecasts = State()


class MyForecasts(StatesGroup):
    groups = State()
    games_1 = State()
    games_2 = State()


class EditForecasts(StatesGroup):
    goals_owner = State()
    goals_guest = State()


class ForecastsSG(StatesGroup):
    group = State()


class ForecastsSecondSG(StatesGroup):
    window_1 = State()
    window_2 = State()
    forecasts = State()


class CalendarSG(StatesGroup):
    window_1 = State()
    window_2 = State()
    window_3 = State()
    window_4 = State()


class RulesSG(StatesGroup):
    start = State()


class TeamSG(StatesGroup):
    start = State()
    team_1 = State()
    team_2 = State()
    team_list = State()


class TableSG(StatesGroup):
    start = State()
