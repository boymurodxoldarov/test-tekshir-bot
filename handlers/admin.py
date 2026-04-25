"""
handlers/admin.py
Admin buyruqlari:
  /addtest KOD javoblar   — test qo'shish / yangilash
  /deltest KOD            — test o'chirish
  /tests                  — barcha testlar ro'yxati
  /admin                  — statistika
"""
import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import ADMIN_ID
from database import (
    add_test,
    delete_test,
    get_all_tests,
    get_admin_stats,
)

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return ADMIN_ID != 0 and user_id == ADMIN_ID


# ─── /addtest ────────────────────────────────
@router.message(Command("addtest"))
async def cmd_addtest(message: Message, command: CommandObject) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return

    args = (command.args or "").strip().split(None, 1)
    if len(args) != 2:
        await message.answer(
            "❌ Format:\n"
            "<code>/addtest TEST_KODI to'g'ri_javoblar</code>\n\n"
            "Masalan:\n"
            "<code>/addtest MATH1 abcdabdcab</code>",
            parse_mode="HTML",
        )
        return

    code, answers = args[0].upper(), args[1]

    # Faqat harf/raqam qabul qilinadi
    clean = answers.lower().replace(" ", "")
    if not clean.isalpha():
        await message.answer(
            "❌ Javoblar faqat harflardan iborat bo'lishi kerak (a-z).",
        )
        return

    is_new = await add_test(code, clean, message.from_user.id)
    if is_new:
        await message.answer(
            f"✅ Test qo'shildi!\n\n"
            f"Kod: <b>{code}</b>\n"
            f"Javoblar: <code>{clean}</code>\n"
            f"Savollar soni: <b>{len(clean)}</b>",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"🔄 Test yangilandi!\n\n"
            f"Kod: <b>{code}</b>\n"
            f"Yangi javoblar: <code>{clean}</code>\n"
            f"Savollar soni: <b>{len(clean)}</b>",
            parse_mode="HTML",
        )


# ─── /deltest ────────────────────────────────
@router.message(Command("deltest"))
async def cmd_deltest(message: Message, command: CommandObject) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return

    code = (command.args or "").strip().upper()
    if not code:
        await message.answer(
            "❌ Format: <code>/deltest TEST_KODI</code>",
            parse_mode="HTML",
        )
        return

    deleted = await delete_test(code)
    if deleted:
        await message.answer(f"🗑 <b>{code}</b> o'chirildi.", parse_mode="HTML")
    else:
        await message.answer(f"❓ <b>{code}</b> topilmadi.", parse_mode="HTML")


# ─── /tests ──────────────────────────────────
@router.message(Command("tests"))
async def cmd_tests(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return

    tests = await get_all_tests()
    if not tests:
        await message.answer(
            "📭 Hozircha testlar yo'q.\n"
            "Qo'shish: <code>/addtest KOD javoblar</code>",
            parse_mode="HTML",
        )
        return

    lines = ["📋 <b>Barcha testlar:</b>\n"]
    for t in tests:
        lines.append(
            f"• <b>{t['code']}</b> — <code>{t['answers']}</code> "
            f"({len(t['answers'])} savol)"
        )

    lines.append(f"\nJami: <b>{len(tests)} ta test</b>")
    await message.answer("\n".join(lines), parse_mode="HTML")


# ─── /admin ──────────────────────────────────
@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return

    s = await get_admin_stats()
    await message.answer(
        "🛠 <b>Admin statistika</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{s['total_users']}</b>\n"
        f"📝 Jami urinishlar: <b>{s['total_submissions']}</b>\n"
        f"📚 Testlar soni: <b>{s['total_tests']}</b>\n"
        f"📊 O'rtacha ball: <b>{s['avg_pct']}%</b>\n"
        f"🔥 Eng mashhur test: <b>{s['popular_test']}</b> "
        f"({s['popular_count']} marta)",
        parse_mode="HTML",
    )
