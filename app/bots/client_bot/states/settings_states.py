from aiogram.fsm.state import State, StatesGroup


class SettingsStates(StatesGroup):
    waiting_value = State()  # field name being edited is stored in FSM data
