from aiogram import Dispatcher

from tgbot.loader import dp
# from .is_admin import AdminFilter
from .inline_text_filter import IsSubcategoryName


if __name__ == "filters":
    dp.filters_factory.bind(IsSubcategoryName)
