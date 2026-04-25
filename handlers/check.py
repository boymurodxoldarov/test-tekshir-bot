"""
handlers/check.py
Foydalanuvchi 'TEST_KODI javoblar' yuborganida ishga tushadi.
"""
import logging

from aiogram import Router
from aiogram.types import Message

from database import get_all_tests, get_or_create_user, get_test, save_result
from services.grader import grade, parse_message
from services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)
router = Router()


def build_result(test_code: str, result: dict) -> str:
    score      = result["score"]
    total      = result["total"]
    percentage = result["percentage"]
    cmap       = result["correct_map"]

    icons = []
    for ok in cmap:
        if ok is True:
            icons.append("✅")
        elif ok is False:
            icons.append("❌")
        else:
            icons.append("⬜")

    if percentage >= 90:
        emoji = "🏆"
    elif percentage >= 70:
        emoji = "🎉"
    elif percentage >= 50:
        emoji = "📝"
    else:
        emoji = "😔"

    icon_row = " ".join(icons)

    return (
        f"{emoji} <b>Test natijasi — {test_code}</b>\n\n"
        f"Ball:  <b>{score}/{total}</b>\n"
        f"Foiz:  <b>{percentage}%</b>\n\n"
        f"{icon_row}"
    )


@router.message()
async def handle_submission(message: Message) -> None:
    if not message.text:
        return

    parsed = parse_message(message.text)
    if parsed is None:
        return

    test_code, user_answers = parsed

    # Test mavjudmi?
    key = await get_test(test_code)
    if key is None:
        tests = await get_all_tests()
        if not tests:
            await message.reply(
                "❓ Hozircha testlar yo'q.\nAdmin test qo'shishi kerak.",
            )
        else:
            avail = ", ".join(f"<code>{t['code']}</code>" for t in tests)
            await message.reply(
                f"❓ Noma'lum test kodi: <b>{test_code}</b>\n"
                f"Mavjud testlar: {avail}",
                parse_mode="HTML",
            )
        return

    # Rate limit
    uid = message.from_user.id
    if not await rate_limiter.is_allowed(uid):
        wait = await rate_limiter.wait_seconds(uid)
        await message.reply(
            f"⏳ Juda tez! <b>{wait} soniya</b> kuting.",
            parse_mode="HTML",
        )
        return

    # Baholash
    result = grade(key, user_answers)

    # Saqlash
    full_name = message.from_user.full_name or "Anonim"
    db_uid = await get_or_create_user(uid, full_name)
    await save_result(
        db_uid,
        test_code,
        result["score"],
        result["total"],
        result["user_norm"],
    )

    await message.reply(build_result(test_code, result), parse_mode="HTML")
