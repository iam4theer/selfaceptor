import asyncio

from telethon import TelegramClient, functions
from telethon.errors import RPCError


# =========================================================
# تنظیمات
# =========================================================

API_ID = 12345678
API_HASH = "YOUR_API_HASH"

SESSION = "telegram_account"


# =========================================================
# Telegram Client
# =========================================================

client = TelegramClient(
    SESSION,
    API_ID,
    API_HASH
)


# =========================================================
# دریافت درخواست‌های در انتظار
# =========================================================

async def get_pending_requests(channel):

    result = await client(
        functions.messages.GetChatInviteImportersRequest(
            peer=channel,
            requested=True,
            limit=100,
            offset_date=None,
            offset_user=functions.InputUserEmpty(),
        )
    )

    return result


# =========================================================
# قبول همه درخواست‌ها
# =========================================================

async def approve_all(channel):

    try:

        print("\n⏳ در حال قبول تمام درخواست‌ها...")

        result = await client(
            functions.messages.HideAllChatJoinRequestsRequest(
                peer=channel,
                approved=True
            )
        )

        print("\n✅ تمام درخواست‌های موجود تأیید شدند.")

        return result

    except RPCError as e:

        print(f"\n❌ خطای تلگرام: {e}")

    except Exception as e:

        print(f"\n❌ خطا: {e}")


# =========================================================
# تعداد درخواست‌ها
# =========================================================

async def show_count(channel):

    try:

        result = await get_pending_requests(channel)

        count = len(result.users)

        print(
            f"\n📊 تعداد درخواست‌های دریافت‌شده: {count}"
        )

        if count > 0:

            print("\nچند درخواست موجود:")

            for user in result.users[:10]:

                name = (
                    f"{user.first_name or ''} "
                    f"{user.last_name or ''}"
                ).strip()

                username = (
                    f"@{user.username}"
                    if user.username
                    else "بدون username"
                )

                print(
                    f"  • {name} | {username} | {user.id}"
                )

        return count

    except RPCError as e:

        print(f"\n❌ خطای تلگرام: {e}")

    except Exception as e:

        print(f"\n❌ خطا: {e}")

    return 0


# =========================================================
# انتخاب کانال
# =========================================================

async def choose_channel():

    dialogs = await client.get_dialogs()

    channels = []

    print("\n======================================")
    print("📢 کانال‌های اکانت")
    print("======================================")

    for dialog in dialogs:

        entity = dialog.entity

        # فقط Channel
        if getattr(entity, "broadcast", False):

            channels.append(entity)

    if not channels:

        print("❌ هیچ کانالی پیدا نشد.")
        return None

    for i, channel in enumerate(channels, 1):

        print(
            f"{i}. {channel.title}"
        )

    print("======================================")

    while True:

        choice = input(
            "\nشماره کانال را وارد کنید: "
        ).strip()

        try:

            index = int(choice) - 1

            if 0 <= index < len(channels):

                return channels[index]

        except ValueError:
            pass

        print("❌ انتخاب نادرست.")


# =========================================================
# منوی کانال
# =========================================================

async def channel_menu(channel):

    print("\n======================================")
    print(f"📢 کانال: {channel.title}")
    print("======================================")

    while True:

        print("\n1️⃣ بررسی درخواست‌ها")
        print("2️⃣ قبول همه درخواست‌ها")
        print("3️⃣ بازگشت")
        print("======================================")

        choice = input(
            "انتخاب: "
        ).strip()

        # -----------------------------------------------
        # تعداد
        # -----------------------------------------------

        if choice == "1":

            await show_count(channel)

        # -----------------------------------------------
        # قبول همه
        # -----------------------------------------------

        elif choice == "2":

            count = await show_count(channel)

            if count == 0:

                print(
                    "\nℹ️ درخواست قابل پردازشی پیدا نشد."
                )

                continue

            print(
                f"\n⚠️ {count} درخواست در لیست فعلی وجود دارد."
            )

            confirm = input(
                "آیا همه تأیید شوند؟ (y/n): "
            ).lower().strip()

            if confirm == "y":

                await approve_all(channel)

            else:

                print("لغو شد.")

        # -----------------------------------------------
        # خروج
        # -----------------------------------------------

        elif choice == "3":

            break

        else:

            print("❌ گزینه نادرست.")


# =========================================================
# Main
# =========================================================

async def main():

    print("======================================")
    print(" Telegram Join Request Manager")
    print("======================================")

    # اولین اجرا:
    # شماره تلفن، کد ورود و در صورت فعال بودن
    # Two-Step Verification را می‌خواهد.

    await client.start()

    me = await client.get_me()

    print(
        f"\n✅ وارد شدید: "
        f"{me.first_name or ''} "
        f"{me.last_name or ''}"
    )

    while True:

        channel = await choose_channel()

        if channel is None:

            return

        await channel_menu(channel)

        again = input(
            "\nکانال دیگری؟ (y/n): "
        ).lower().strip()

        if again != "y":

            break

    print("\n👋 پایان برنامه.")


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    with client:

        client.loop.run_until_complete(
            main()
        )
