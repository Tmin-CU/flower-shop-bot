from aiogram import F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
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
    "spring_bouquets": "Весенние букеты",
}


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог", callback_data="catalog_budgets")],
            [InlineKeyboardButton(text="О магазине", callback_data="about_shop")],
        ]
    )
    await message.answer(
        "Добро пожаловать в цветочный магазин🌸. Выберите нужный раздел:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "about_shop")
async def about_shop(callback: CallbackQuery):
    text = (
        "Мы — студия флористики.\n"
        "Собираем свежие букеты и доставляем их точно ко времени.\n\n"
        "График работы: 09:00 - 21:00\n"
        "Телефон: +7 (999) 000-00-00"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="start_menu")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "start_menu")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог", callback_data="catalog_budgets")],
            [InlineKeyboardButton(text="О магазине", callback_data="about_shop")],
        ]
    )
    await callback.message.edit_text("Выберите нужный раздел:", reply_markup=kb)


@router.callback_query(F.data == "catalog_budgets")
async def show_budgets(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Весенний сад", callback_data="cat_garden_0_0")],
            [InlineKeyboardButton(text="Корзины и Кашпо", callback_data="cat_baskets_0_0")],
            [InlineKeyboardButton(text="Ведра", callback_data="cat_buckets_0_0")],
            [InlineKeyboardButton(text="Ведерки и корзинки", callback_data="cat_small_baskets_0_0")],
            [InlineKeyboardButton(text="Тюльпаны", callback_data="cat_tulips_0_0")],
            [InlineKeyboardButton(text="Свертки тюльпанов", callback_data="cat_tulip_wraps_0_0")],
            [InlineKeyboardButton(text="Сибирские розы", callback_data="cat_roses_0_0")],
            [InlineKeyboardButton(text="Весенние букеты", callback_data="cat_spring_bouquets_0_0")],
            [InlineKeyboardButton(text="Назад", callback_data="start_menu")],
        ]
    )
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer("Выберите категорию:", reply_markup=kb)
    else:
        await callback.message.edit_text("Выберите категорию:", reply_markup=kb)


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    parts = callback.data.split("_")
    # Categories with underscore in name: tulip_wraps, small_baskets, spring_bouquets
    if len(parts) > 4:
        category = f"{parts[1]}_{parts[2]}"
        page = int(parts[3])
        photo_idx = int(parts[4])
    else:
        category = parts[1]
        page = int(parts[2])
        photo_idx = int(parts[3])

    product = await db.get_product_by_category(category, page)
    total_products = await db.count_products_by_category(category)

    if not product:
        return await callback.answer("В этой категории пока нет товаров.", show_alert=True)

    p_id, p_name, p_price, p_desc, p_photos = product
    all_photos = p_photos.split("|")
    current_photo = all_photos[photo_idx] if photo_idx < len(all_photos) else all_photos[0]

    display_name = (
        p_name if category in ("tulip_wraps", "roses") else CAT_NAMES.get(category, p_name)
    )
    caption = f"<b>{display_name}</b>\n\nЦена: {p_price} руб.\n\n{p_desc}"

    nav_btns = []
    if page > 0:
        nav_btns.append(
            InlineKeyboardButton(text="⬅️ Товар", callback_data=f"cat_{category}_{page - 1}_0")
        )
    if page < total_products - 1:
        nav_btns.append(
            InlineKeyboardButton(text="Товар ➡️", callback_data=f"cat_{category}_{page + 1}_0")
        )

    photo_btns = []
    if len(all_photos) > 1:
        prev_idx = (photo_idx - 1) % len(all_photos)
        next_idx = (photo_idx + 1) % len(all_photos)
        photo_btns = [
            InlineKeyboardButton(
                text="‹", callback_data=f"cat_{category}_{page}_{prev_idx}"
            ),
            InlineKeyboardButton(
                text=f"{photo_idx + 1}/{len(all_photos)}", callback_data="ignore"
            ),
            InlineKeyboardButton(
                text="›", callback_data=f"cat_{category}_{page}_{next_idx}"
            ),
        ]

    kb_list = [
        [InlineKeyboardButton(text="Оформить заказ", callback_data=f"buy_{p_id}")]
    ]
    if photo_btns:
        kb_list.append(photo_btns)
    if nav_btns:
        kb_list.append(nav_btns)
    kb_list.append(
        [InlineKeyboardButton(text="К категориям", callback_data="catalog_budgets")]
    )
    kb = InlineKeyboardMarkup(inline_keyboard=kb_list)

    if not callback.message.photo:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=current_photo, caption=caption, reply_markup=kb, parse_mode="HTML"
        )
    else:
        media = InputMediaPhoto(media=current_photo, caption=caption, parse_mode="HTML")
        await callback.message.edit_media(media=media, reply_markup=kb)


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def start_order(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    await state.update_data(product_id=product_id)
    await state.set_state(OrderFlow.waiting_for_phone)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_order")]
        ]
    )
    await callback.message.answer(
        "Пожалуйста, введите ваш номер телефона:", reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог", callback_data="catalog_budgets")],
            [InlineKeyboardButton(text="О магазине", callback_data="about_shop")],
        ]
    )
    await callback.message.edit_text("Заказ отменён. Выберите нужный раздел:", reply_markup=kb)


@router.message(OrderFlow.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(OrderFlow.waiting_for_address)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_order")]
        ]
    )
    await message.answer("Введите адрес доставки:", reply_markup=kb)


@router.message(OrderFlow.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(OrderFlow.waiting_for_date)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_order")]
        ]
    )
    await message.answer(
        "Введите желаемую дату доставки (например, 01.03.2026):", reply_markup=kb
    )


@router.message(OrderFlow.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    data = await state.get_data()
    product_name = await db.get_product_name(data["product_id"])
    summary = (
        f"<b>Ваш заказ:</b>\n\n"
        f"Товар: {product_name}\n"
        f"Телефон: {data['phone']}\n"
        f"Адрес: {data['address']}\n"
        f"Дата доставки: {data['date']}\n\n"
        "Подтвердить заказ?"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order"),
            ]
        ]
    )
    await state.set_state(OrderFlow.confirm)
    await message.answer(summary, reply_markup=kb, parse_mode="HTML")


@router.callback_query(OrderFlow.confirm, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    order_id = await db.create_order(
        user_id=user.id,
        user_name=user.full_name,
        phone=data["phone"],
        address=data["address"],
        date=data["date"],
        product_id=data["product_id"],
    )
    await state.clear()

    product_name = await db.get_product_name(data["product_id"])
    admin_text = (
        f"🆕 <b>Новый заказ #{order_id}</b>\n\n"
        f"Клиент: {user.full_name} (id: {user.id})\n"
        f"Товар: {product_name}\n"
        f"Телефон: {data['phone']}\n"
        f"Адрес: {data['address']}\n"
        f"Дата доставки: {data['date']}"
    )
    kb_admin = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнен", callback_data=f"complete_{order_id}"
                )
            ]
        ]
    )
    try:
        await callback.bot.send_message(
            ADMIN_ID, admin_text, reply_markup=kb_admin, parse_mode="HTML"
        )
    except Exception:
        pass

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог", callback_data="catalog_budgets")]
        ]
    )
    await callback.message.edit_text(
        f"✅ Заказ #{order_id} принят! Мы свяжемся с вами по номеру {data['phone']}.",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("complete_"))
async def complete_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    await db.mark_order_completed(order_id)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Заказ выполнен.</b>", parse_mode="HTML"
    )
    await callback.answer("Заказ отмечен как выполненный.")
