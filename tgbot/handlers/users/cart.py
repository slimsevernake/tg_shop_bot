from pprint import pprint

from aiogram import types
from aiogram.dispatcher import FSMContext

from tgbot.keyboards.inline.callback_datas import buy_callback, liked_product, edit_quantity
from tgbot.keyboards.inline.gen_keyboard import cart_edit_kb, KeyboardGen, CartKeyboardGen
from tgbot.loader import dp, bot
from tgbot.states.cart_states import ProductStates
from decimal import Decimal

from tgbot.utils.cart_product_utils import create_cart_list, check_quantity, wipe_cart_data
from tgbot.utils.db_api.quick_commands import get_product


async def update_product_info(product_id: int, state: FSMContext):

    async with state.proxy() as state_data:
        # state_data["product_info"].update({
        #     "product_id": product.id,
        #     "product_title": product.title,
        #     "product_price": str(product.price),
        #     "category_id": product.parent.category_id,
        #     "subcategory_name": product.parent.tg_name,
        # })
        if str(product_id) not in state_data['products'].keys():
            product = await get_product(product_id)
            products = {
                str(product.id):
                    {
                        "title": product.title,
                        "quantity": 0,
                        "price": str(product.price),
                        "total": "0.00",
                    },
            }
            state_data['products'].update(products)
    return True


def product_total_price(state_data: dict):
    products_list = state_data.get("products")
    result = str(products_list[state_data.get("product_id")]['quantity'] * Decimal(
        products_list[state_data.get("product_id")]['price']))
    return result


@dp.callback_query_handler(buy_callback.filter())
async def add_to_cart(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = callback_data.get("product_id")
    await update_product_info(int(product_id), state)
    async with state.proxy() as state_data:
        state_data["product_id"] = product_id
        state_data["products"][product_id]["quantity"] += 1
        state_data["products"][product_id]["total"] = product_total_price(state_data=state_data)
        keyboard = await KeyboardGen.from_product_id(product_id=int(product_id), data=state_data)
        markup = keyboard.build_edit_kb()
    print("=" * 100)
    pprint(await state.get_data())
    await bot.edit_message_reply_markup(inline_message_id=call.inline_message_id, reply_markup=markup)


@dp.callback_query_handler(edit_quantity.filter(edit="True", add="False", reduce="False"))
async def edit_product_quantity(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = callback_data.get("product_id")
    await update_product_info(int(product_id), state)
    await bot.send_message(chat_id=call.from_user.id, text="?????????????? ???????????????????? ???????????? ???? ?????????????? ???????????? ????????????????")
    await state.update_data(message_data=dict(call))
    await state.update_data(product_id=product_id)
    await ProductStates.QUANTITY_EDIT.set()


@dp.message_handler(state=ProductStates.QUANTITY_EDIT)
async def accept_product_quantity(message: types.Message, state: FSMContext):
    if not await check_quantity(message=message):
        return
    async with state.proxy() as state_data:
        quantity = int(message.text)
        product_id = state_data.get("product_id")
        inline_message_id = state_data.get("message_data")["inline_message_id"]
        products_list = state_data.get("products")
        products_list[product_id]['quantity'] = quantity
        products_list[product_id]['total'] = product_total_price(state_data)
        keyboard = await KeyboardGen.from_product_id(product_id=int(product_id), data=state_data)
        markup = keyboard.build_edit_kb()
        await bot.edit_message_reply_markup(inline_message_id=inline_message_id, reply_markup=markup)
        del state_data['message_data']
    pprint(await state.get_data())
    await message.answer("??????????????")
    await state.reset_state(with_data=False)


@dp.callback_query_handler(edit_quantity.filter(edit="True", add="True"))
@dp.callback_query_handler(edit_quantity.filter(edit="True", reduce="True"))
async def plus_one_quantity(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = callback_data.get("product_id")
    await update_product_info(int(product_id), state)
    async with state.proxy() as state_data:
        state_data['product_id'] = product_id
        products_list = state_data.get("products")
        product_quantity = products_list[product_id]['quantity']
        if product_quantity == 0 and callback_data.get("reduce") == "True":
            await call.answer(text="?? ?????? ???????? ?????????? ???????????? ?? ??????????????")
            return
        elif callback_data.get("reduce") == "True":
            products_list[product_id]['quantity'] -= 1
            await call.answer(text="?????????????? ???? ??????????????")
        elif callback_data.get("add") == "True":
            products_list[product_id]['quantity'] += 1
            await call.answer(text="?????????????????? ?? ??????????????")
        products_list[product_id]['total'] = product_total_price(state_data)
        keyboard = await KeyboardGen.from_product_id(product_id=int(product_id), data=state_data)
        markup = keyboard.build_edit_kb()
    await bot.edit_message_reply_markup(inline_message_id=call["inline_message_id"],
                                        reply_markup=markup)
    pprint(await state.get_data())


@dp.callback_query_handler(liked_product.filter())
async def add_liked(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    product_id = int(callback_data.get("product_id"))
    async with state.proxy() as state_data:
        if callback_data.get("delete") == "False":
            state_data["liked_products"].append(product_id)
            await call.answer("?????????????????? ?? ??????????????????")
        elif callback_data.get("add") == "False":
            for count, value in enumerate(state_data['liked_products']):
                if value == product_id:
                    del state_data["liked_products"][count]
            await call.answer("?????????????? ???? ??????????????????")
        keyboard = await KeyboardGen.from_product_id(product_id=product_id, data=state_data)
        markup = keyboard.build_product_kb()
    await bot.edit_message_reply_markup(inline_message_id=call["inline_message_id"], reply_markup=markup)
    pprint(await state.get_data())


@dp.callback_query_handler(text='show_cart')
async def show_cart(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as state_data:
        if not state_data.get("products"):
            await call.answer("?????????????? ??????????")
            return
    answer = await create_cart_list(state)
    await call.answer()
    await bot.send_message(chat_id=call.from_user.id, text=answer, reply_markup=cart_edit_kb)


@dp.callback_query_handler(text="wipe_cart")
async def wipe_cart(call: types.CallbackQuery, state: FSMContext):
    await wipe_cart_data(state, products=True)
    await bot.edit_message_text(text="?????????????? ??????????????", chat_id=call.from_user.id,
                                message_id=call.message.message_id)
    await call.answer()


@dp.callback_query_handler(text="edit_cart")
async def edit_cart(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as state_data:
        product_id = int(list(state_data['products'].keys())[0])
        product = await get_product(product_id=product_id)
        cart_product = state_data['products'][str(product_id)]
        keyboard = CartKeyboardGen(data=state_data)
        markup = keyboard.build_pagination_keyboard()
        caption = cart_product['title'] + "\n\n" + str(cart_product['quantity']) + " ????. x $" + cart_product['price'] \
                  + " = $" + cart_product['total']
    await call.message.answer_photo(photo=product.image, caption=caption, reply_markup=markup)
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    await call.answer()
