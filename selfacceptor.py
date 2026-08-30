import asyncio

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ==================================================
# تنظیمات
# ==================================================

BOT_TOKEN = "8925977547:AAGEx8nKIaYkWILg7wxeAG-Ovb6XmcVcxu4"


# ==================================================
# راه‌اندازی
# ==================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

dp.include_router(router)


# ==================================================
# پنل کانال
# ==================================================

def channel_panel(channel_id: int):

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="📊 تعداد درخواست‌ها",
        callback_data=f"count:{channel_id}"
    )

    keyboard.button(
        text="✅ قبول همه درخواست‌ها",
        callback_data=f"approve:{channel_id}"
    )

    keyboard.adjust(1)

    return keyboard.as_markup()


# ==================================================
# /start
# ==================================================

@router.message(Command("start"))
async def start(message: Message):

    await message.answer(
        "🤖 ربات مدیریت درخواست عضویت\n\n"
        "برای شروع، ربات را در کانال خود ادمین کنید.\n\n"
        "بعد از آن، آیدی عددی کانال را برای من بفرستید.\n\n"
        "مثال:\n"
        "`-1001234567890`",
        parse_mode="Markdown"
    )


# ==================================================
# دریافت Channel ID
# ==================================================

@router.message(F.text)
async def channel_id_handler(message: Message):

    text = message.text.strip()

    # فقط Channel ID عددی
    if not text.startswith("-100"):
        return

    try:
        channel_id = int(text)

    except ValueError:
        await message.answer("❌ آیدی کانال نادرست است.")
        return

    user_id = message.from_user.id

    try:

        # بررسی عضویت/ادمین بودن کاربر
        user_member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=user_id
        )

        if user_member.status not in ("administrator", "creator"):

            await message.answer(
                "❌ شما ادمین این کانال نیستید."
            )
            return

        # بررسی ادمین بودن ربات
        bot_info = await bot.get_me()

        bot_member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=bot_info.id
        )

        if bot_member.status not in ("administrator", "creator"):

            await message.answer(
                "❌ ربات در این کانال ادمین نیست.\n\n"
                "اول ربات را ادمین کانال کنید."
            )
            return

        # بررسی اجازه مدیریت درخواست‌ها
        if (
            bot_member.status == "administrator"
            and not getattr(
                bot_member,
                "can_invite_users",
                False
            )
        ):

            await message.answer(
                "❌ ربات اجازه مدیریت درخواست‌های عضویت را ندارد.\n\n"
                "در تنظیمات ادمین کانال، "
                "اجازه «Invite Users» را فعال کنید."
            )
            return

        await message.answer(
            "✅ کانال تأیید شد.\n\n"
            f"📢 Channel ID:\n`{channel_id}`\n\n"
            "پنل مدیریت:",
            parse_mode="Markdown",
            reply_markup=channel_panel(channel_id)
        )

    except Exception as e:

        print("ERROR:", e)

        await message.answer(
            "❌ نتوانستم کانال را بررسی کنم.\n\n"
            "مطمئن شوید Channel ID درست است و "
            "ربات در کانال ادمین است."
        )


# ==================================================
# بررسی دوباره دسترسی
# ==================================================

async def check_access(channel_id: int, user_id: int):

    try:

        user = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=user_id
        )

        bot_info = await bot.get_me()

        bot_member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=bot_info.id
        )

        user_is_admin = user.status in (
            "administrator",
            "creator"
        )

        bot_is_admin = bot_member.status in (
            "administrator",
            "creator"
        )

        return user_is_admin and bot_is_admin

    except Exception:

        return False


# ==================================================
# تعداد درخواست‌ها
# ==================================================

@router.callback_query(F.data.startswith("count:"))
async def count_requests(callback: CallbackQuery):

    channel_id = int(
        callback.data.split(":")[1]
    )

    user_id = callback.from_user.id

    if not await check_access(channel_id, user_id):

        await callback.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    try:

        requests = await bot.get_chat_join_requests(
            chat_id=channel_id,
            limit=100
        )

        count = len(requests)

        await callback.answer()

        await callback.message.edit_text(
            "📊 درخواست‌های موجود:\n\n"
            f"👥 {count} درخواست",
            reply_markup=channel_panel(channel_id)
        )

    except Exception as e:

        print("ERROR:", e)

        await callback.answer(
            "❌ خطا در دریافت درخواست‌ها.",
            show_alert=True
        )


# ==================================================
# قبول همه درخواست‌ها
# ==================================================

@router.callback_query(F.data.startswith("approve:"))
async def approve_all(callback: CallbackQuery):

    channel_id = int(
        callback.data.split(":")[1]
    )

    user_id = callback.from_user.id

    if not await check_access(channel_id, user_id):

        await callback.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await callback.answer()

    await callback.message.edit_text(
        "⏳ در حال قبول کردن درخواست‌ها...\n\n"
        "لطفاً صبر کنید."
    )

    approved = 0
    failed = 0

    try:

        while True:

            requests = await bot.get_chat_join_requests(
                chat_id=channel_id,
                limit=100
            )

            if not requests:
                break

            for request in requests:

                try:

                    await bot.approve_chat_join_request(
                        chat_id=channel_id,
                        user_id=request.user.id
                    )

                    approved += 1

                except Exception as e:

                    failed += 1
                    print(
                        f"Failed {request.user.id}: {e}"
                    )

                await asyncio.sleep(0.1)

        await callback.message.edit_text(
            "✅ عملیات تمام شد.\n\n"
            f"👥 قبول‌شده: {approved}\n"
            f"❌ ناموفق: {failed}",
            reply_markup=channel_panel(channel_id)
        )

    except Exception as e:

        print("ERROR:", e)

        await callback.message.edit_text(
            f"❌ خطا:\n\n{e}",
            reply_markup=channel_panel(channel_id)
        )


# ==================================================
# اجرای ربات
# ==================================================

async def main():

    print("🤖 Bot is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())