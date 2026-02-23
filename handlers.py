import re
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from config import ADMIN_ID
from states import OrderFlow
import database as db

router = Router()

CAT_NAMES = {
    "garden": "Весенний сад",
    "baskets": "Корзины и Кашпо",
    "buckets": "Ведра",
    "small_baskets": "Ведерки и корзинки",
    "tulips": "Тюльпаны",
    "tulip_wraps": "Свертки тюльпанов",
    "roses": "Сибирские розы",
    "spring_bouquets": "Весенние букеты"
}

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Каталог", callback_data="catalog_budgets")],
        [InlineKeyboardButton(text="О магазине", callback_data="about_shop")]
    ])
    await message.answer("Добро пожаловать в цветочный магазин🌸. Выберите нужный раздел:", reply_markup=kb)

@router.callback_query(F.data == "about_shop")
async def about_shop(callback: CallbackQuery):
    text = (
        "Мы — студия флористики.\n"
        "Собираем свежие букеты и доставляем их точно ко времени.\n\n"
        "График работы: 09:00 - 21:00\n"
        "Телефон: +7 (999) 000-00-00"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="start_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data == "start_menu")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Каталог", callback_data="catalog_budgets")],
        [InlineKeyboardButton(text="О магазине", callback_data="about_shop")]
    ])
    await callback.message.edit_text("Выберите нужный раздел:", reply_markup=kb)

@router.callback_query(F.data == "catalog_budgets")
async def show_budgets(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Весенний сад", callback_data="cat_garden_0_0")],
        [InlineKeyboardButton(text="Корзины и Кашпо", callback_data="cat_baskets_0_0")],
        [InlineKeyboardButton(text="Ведра", callback_data="cat_buckets_0_0")],
        [InlineKeyboardButton(text="Ведерки и корзинки", callback_data="cat_small_baskets_0_0")],
        [InlineKeyboardButton(text="Тюльпаны", callback_data="cat_tulips_0_0")],
        [InlineKeyboardButton(text="Свертки тюльпанов", callback_data="cat_tulip_wraps_0_0")],
        [InlineKeyboardButton(text="Сибирские розы", callback_data="cat_roses_0_0")],
        [InlineKeyboardButton(text="Весенние букеты", callback_data="cat_spring_bouquets_0_0")],
        [InlineKeyboardButton(text="Назад", callback_data="start_menu")]
    ])
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer("Выберите категорию:", reply_markup=kb)
    else:
        await callback.message.edit_text("Выберите категорию:", reply_markup=kb)

@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) > 4:
        category = f"{parts[1]}_{parts[2]}"
        page = int(parts[3])
    else:
        category = parts[1]
        page = int(parts[2])

    product = await db.get_product_by_category(category, page)
    total_products = await db.count_products_by_category(category)

    if not product:
        return await callback.answer("В этой категории пока нет товаров.", show_alert=True)

    p_id, p_name, p_price, p_desc, p_photos = product
    all_photos = p_photos.split("|")\n    
display_name = p_name if category in ["tulip_wraps", "roses"] else CAT_NAMES.get(category, p_name)
    caption = f"<b>{display_name}</b>\n\nЦена: {p_price} руб.\n\n{p_desc}"

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ Пред. товар", callback_data=f"cat_{category}_{page-1}_0"))
    if page < total_products - 1:
        nav_btns.append(InlineKeyboardButton(text="След. товар ➡️", callback_data=f"cat_{category}_{page+1}_0"))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оформить заказ", callback_data=f"buy_{p_id}")],
        nav_btns,
        [InlineKeyboardButton(text="К категориям", callback_data="catalog_budgets")]
    ])

    await callback.message.delete()

    if len(all_photos) > 1:
        media_group = []
        for i, photo_id in enumerate(all_photos):
            if i == 0:
                media_group.append(InputMediaPhoto(media=photo_id, caption=caption, parse_mode="HTML"))
            else:
                media_group.append(InputMediaPhoto(media=photo_id))
        
        await callback.message.answer_media_group(media=media_group)
        await callback.message.answer("Выберите действие:", reply_markup=kb)
    else:
        await callback.message.answer_photo(photo=all_photos[0], caption=caption, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("buy_"))
async def start_order(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    await state.update_data(product_id=product_id)
    await callback.message.answer("Введите ваш номер телефона (в формате +7...):")
    await state.set_state(OrderFlow.waiting_for_phone)

@router.message(OrderFlow.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if not re.match(r'^\+?[78][-\(]?\d{3}\)?-?\d{3}-?\d{2}-?\d{2}$', message.text.strip()):
        return await message.answer("Некорректный формат. Пожалуйста, введите номер телефона корректно.")
    await state.update_data(phone=message.text.strip())
    await message.answer("Укажите адрес доставки (улица, дом, квартира):")
    await state.set_state(OrderFlow.waiting_for_address)

@router.message(OrderFlow.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        return await message.answer("Адрес слишком короткий. Пожалуйста, укажите полные данные.")
    await state.update_data(address=message.text.strip())
    await message.answer("Укажите дату и время доставки (например: 8 марта, 12:00):")
    await state.set_state(OrderFlow.waiting_for_date)

@router.message(OrderFlow.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    if len(message.text.strip()) < 3:
        return await message.answer("Пожалуйста, укажите корректную дату и время.")
    await state.update_data(date=message.text.strip())
    data = await state.get_data()
    text = (
        "<b>Проверьте данные заказа:</b>\n\n"
        f"Телефон: {data['phone']}\n"
        f"Адрес: {data['address']}\n"
        f"Дата и время: {data['date']}\n\n"
        "Подтверждаете заказ?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="Изменить данные", callback_data="confirm_no")]
    ])
    await message.answer(text, reply_markup=kb)
    await state.set_state(OrderFlow.confirm_order)

@router.callback_query(OrderFlow.confirm_order, F.data == "confirm_no")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Оформление отменено.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Каталог", callback_data="catalog_budgets")],
        [InlineKeyboardButton(text="О магазине", callback_data="about_shop")]
    ])
    await callback.message.answer("Выберите нужный раздел:", reply_markup=kb)

@router.callback_query(OrderFlow.confirm_order, F.data == "confirm_yes")
async def finish_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    order_id = await db.create_order(
        user.id, user.first_name, data['phone'], data['address'], data['date'], data['product_id']
    )
    product_name = await db.get_product_name(data['product_id'])
    await callback.message.edit_text("Ваш заказ успешно оформлен. Менеджер свяжется с вами при необходимости.")
    await state.clear()
    admin_text = (
        f"<b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
        f"Товар: {product_name}\n"
        f"Клиент: <a href='tg://user?id={user.id}'>{user.first_name}</a>\n"
        f"Телефон: <code>{data['phone']}</code>\n"
        f"Адрес: {data['address']}\n"
        f"Дата: {data['date']}"
    )
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отметить как выполненный", callback_data=f"done_{order_id}")],
        [InlineKeyboardButton(text="Написать клиенту", url=f"tg://user?id={user.id}")]
    ])
    try:
        await callback.bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_kb)
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")

@router.callback_query(F.data.startswith("done_"))
async def mark_order_done(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("У вас нет прав.", show_alert=True)
    order_id = int(callback.data.split("_")[1])
    await db.mark_order_completed(order_id)
    old_text = callback.message.html_text
    new_text = f"<b>[ВЫПОЛНЕН]</b>\n{old_text}"
    await callback.message.edit_text(new_text, reply_markup=None)

@router.message(F.photo)
async def get_photo_id(message: Message):
    photo_id = message.photo[-1].file_id
    text = (
        "ID этой фотографии:\n\n"
        f"<code>{photo_id}</code>\n\n"
        "Нажмите на ID, чтобы скопировать его."
    )
    await message.answer(text)