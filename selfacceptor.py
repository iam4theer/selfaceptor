import asyncio
import os
import re

from telethon import TelegramClient, functions
from telethon.errors import (
    ApiIdInvalidError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
    RPCError,
)
from telethon.tl.types import Channel


# =========================================================
# CONFIG
# =========================================================

API_ID = 32553007
API_HASH = "a18a9a0eafeb8a93a6f97bd161e56856"

SESSION_DIR = "sessions"

os.makedirs(SESSION_DIR, exist_ok=True)


# =========================================================
# INPUT
# =========================================================

def clean_input(value):
    """
    حذف کاراکترهای مخفی/غیرقابل چاپ از ورودی ترمینال.
    """
    if value is None:
        return ""

    value = value.strip()

    # فقط اعداد انگلیسی را نگه می‌داریم
    digits = re.findall(r"[0-9]", value)

    if digits:
        return "".join(digits)

    return value


# =========================================================
# LOGIN
# =========================================================

async def login():

    phone = input(
        "\n📱 شماره Telegram را وارد کنید:\n> "
    ).strip()

    if not phone:
        print("❌ شماره وارد نشده.")
        return None

    session_name = re.sub(
        r"[^0-9+]",
        "",
        phone
    ).replace("+", "")

    session_path = os.path.join(
        SESSION_DIR,
        session_name
    )

    client = TelegramClient(
        session_path,
        API_ID,
        API_HASH
    )

    try:

        await client.connect()

        if not await client.is_user_authorized():

            print(
                "\n📨 در حال ارسال کد ورود..."
            )

            await client.send_code_request(
                phone
            )

            code = input(
                "\n🔐 کد Telegram را وارد کنید:\n> "
            ).strip()

            try:

                await client.sign_in(
                    phone=phone,
                    code=code
                )

            except SessionPasswordNeededError:

                password = input(
                    "\n🔑 رمز Two-Step Verification:\n> "
                )

                await client.sign_in(
                    password=password
                )

        me = await client.get_me()

        print(
            "\n======================================"
        )
        print("✅ ورود موفق بود")
        print(
            f"👤 {me.first_name or ''} "
            f"{me.last_name or ''}"
        )
        print(
            "======================================"
        )

        return client

    except ApiIdInvalidError:

        print(
            "\n❌ API_ID یا API_HASH نادرست است."
        )

    except PhoneNumberInvalidError:

        print(
            "\n❌ شماره تلفن نادرست است."
        )

    except PhoneCodeInvalidError:

        print(
            "\n❌ کد Telegram نادرست است."
        )

    except Exception as e:

        print(
            f"\n❌ خطا در Login:\n{e}"
        )

    return None


# =========================================================
# GET CHANNELS
# =========================================================

async def get_channels(client):

    dialogs = await client.get_dialogs()

    channels = []

    for dialog in dialogs:

        entity = dialog.entity

        if isinstance(entity, Channel):

            if getattr(
                entity,
                "broadcast",
                False
            ):

                channels.append(entity)

    return channels


# =========================================================
# SHOW CHANNELS
# =========================================================

async def choose_channel(client):

    channels = await get_channels(client)

    if not channels:

        print(
            "\n❌ هیچ کانالی پیدا نشد."
        )

        return None

    print(
        "\n======================================"
    )
    print("📢 کانال‌های اکانت")
    print(
        "======================================"
    )

    for number, channel in enumerate(
        channels,
        start=1
    ):

        print(
            f"{number}. {channel.title}"
        )

    print(
        "======================================"
    )

    while True:

        raw = input(
            "\nشماره کانال را وارد کنید:\n> "
        )

        # حل مشکل کاراکتر مخفی ترمینال
        digits = re.findall(
            r"[0-9]",
            raw
        )

        if not digits:

            print(
                "❌ فقط شماره کانال را وارد کنید."
            )

            continue

        try:

            number = int(
                "".join(digits)
            )

        except ValueError:

            print(
                "❌ شماره نادرست."
            )

            continue

        if 1 <= number <= len(channels):

            return channels[number - 1]

        print(
            f"❌ عدد باید بین 1 تا {len(channels)} باشد."
        )


# =========================================================
# GET PENDING REQUESTS
# =========================================================

async def get_pending_requests(
    client,
    channel
):

    try:

        result = await client(
            functions.messages.GetChatInviteImportersRequest(
                peer=channel,
                requested=True,
                limit=100,
                offset_date=None,
                offset_user=None,
            )
        )

        return result

    except RPCError as e:

        print(
            f"\n❌ خطای Telegram:\n{e}"
        )

    except Exception as e:

        print(
            f"\n❌ خطا:\n{e}"
        )

    return None


# =========================================================
# COUNT REQUESTS
# =========================================================

async def show_request_count(
    client,
    channel
):

    result = await get_pending_requests(
        client,
        channel
    )

    if result is None:
        return None

    count = len(result.users)

    print(
        "\n======================================"
    )

    print(
        f"📊 درخواست‌های در انتظار: {count}"
    )

    print(
        "======================================"
    )

    return count


# =========================================================
# APPROVE ALL
# =========================================================

async def approve_all(
    client,
    channel
):

    try:

        print(
            "\n⏳ در حال قبول تمام درخواست‌ها..."
        )

        await client(
            functions.messages.HideAllChatJoinRequestsRequest(
                peer=channel,
                approved=True
            )
        )

        print(
            "\n✅ عملیات موفقانه انجام شد."
        )

        return True

    except RPCError as e:

        print(
            f"\n❌ خطای Telegram:\n{e}"
        )

    except Exception as e:

        print(
            f"\n❌ خطا:\n{e}"
        )

    return False


# =========================================================
# CHANNEL MENU
# =========================================================

async def channel_menu(
    client,
    channel
):

    while True:

        print(
            "\n======================================"
        )

        print(
            f"📢 کانال: {channel.title}"
        )

        print(
            "======================================"
        )

        print(
            "\n1️⃣ بررسی درخواست‌ها"
        )

        print(
            "2️⃣ ✅ قبول همه درخواست‌ها"
        )

        print(
            "3️⃣ 🔄 تازه‌سازی"
        )

        print(
            "4️⃣ ◀️ برگشت"
        )

        print(
            "======================================"
        )

        raw = input(
            "انتخاب: "
        )

        # حذف کاراکترهای مخفی
        digits = re.findall(
            r"[0-9]",
            raw
        )

        if not digits:

            print(
                "❌ گزینه نادرست."
            )

            continue

        choice = "".join(digits)

        # -------------------------------------------------
        # COUNT
        # -------------------------------------------------

        if choice == "1":

            await show_request_count(
                client,
                channel
            )

        # -------------------------------------------------
        # APPROVE ALL
        # -------------------------------------------------

        elif choice == "2":

            print(
                "\n⚠️ این گزینه تمام درخواست‌های "
                "در انتظار این کانال را تأیید می‌کند."
            )

            confirm = input(
                "ادامه؟ (y/n): "
            ).strip().lower()

            if confirm in (
                "y",
                "yes"
            ):

                await approve_all(
                    client,
                    channel
                )

            else:

                print(
                    "❌ لغو شد."
                )

        # -------------------------------------------------
        # REFRESH
        # -------------------------------------------------

        elif choice == "3":

            continue

        # -------------------------------------------------
        # BACK
        # -------------------------------------------------

        elif choice == "4":

            break

        else:

            print(
                "❌ گزینه نادرست."
            )


# =========================================================
# MAIN MENU
# =========================================================

async def main_menu(client):

    while True:

        print(
            "\n======================================"
        )

        print(
            "🤖 Telegram Join Request Manager"
        )

        print(
            "======================================"
        )

        print(
            "\n1️⃣ 📢 کانال‌های من"
        )

        print(
            "2️⃣ 🔄 تازه‌سازی"
        )

        print(
            "3️⃣ ❌ خروج"
        )

        print(
            "======================================"
        )

        raw = input(
            "انتخاب: "
        )

        digits = re.findall(
            r"[0-9]",
            raw
        )

        if not digits:

            print(
                "❌ گزینه نادرست."
            )

            continue

        choice = "".join(digits)

        # -------------------------------------------------
        # CHANNELS
        # -------------------------------------------------

        if choice == "1":

            channel = await choose_channel(
                client
            )

            if channel:

                await channel_menu(
                    client,
                    channel
                )

        # -------------------------------------------------
        # REFRESH
        # -------------------------------------------------

        elif choice == "2":

            channels = await get_channels(
                client
            )

            print(
                f"\n📢 تعداد کانال‌ها: "
                f"{len(channels)}"
            )

        # -------------------------------------------------
        # EXIT
        # -------------------------------------------------

        elif choice == "3":

            print(
                "\n👋 برنامه بسته شد."
            )

            break

        else:

            print(
                "❌ گزینه نادرست."
            )


# =========================================================
# MAIN
# =========================================================

async def main():

    client = await login()

    if client is None:

        return

    try:

        await main_menu(client)

    finally:

        await client.disconnect()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    asyncio.run(main())
