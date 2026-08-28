from aiogram.fsm.state import State, StatesGroup


class AddSlotStates(StatesGroup):
    waiting_times = State()  # a date has been picked via the calendar; waiting for time lines
