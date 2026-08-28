from aiogram.fsm.state import State, StatesGroup


class ConnectBotStates(StatesGroup):
    waiting_for_token = State()
