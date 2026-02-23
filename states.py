from aiogram.fsm.state import StatesGroup, State


class OrderFlow(StatesGroup):
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_date = State()
    confirm = State()
