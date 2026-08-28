from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_date = State()
    waiting_time = State()
    confirm = State()
