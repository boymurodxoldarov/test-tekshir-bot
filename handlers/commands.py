"""
handlers/commands.py — Foydalanuvchi buyruqlari
"""
import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from database import (
    get_all_tests,
    get_leaderboard,
    get_or_create_user,
    get_user_history,
    get_user_stats,
)

logger = logging.getLogger(__name__)
router = Router()


# ─── /start ──────────────────────────────────
@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    user = message.from_user
    await get_or_create_user(user.id, user.full_name or "Anonim")

    tests = await get_all_tests()
    if tests:
        test_list = "  ".join(f"<code>{t['code']}</code>" for t in tests)
        tests_section = f"\n<b>Mavjud testlar:</b> {test_list}\n"
    else:
        tests_section = "\n<i>Hozircha testlar yo'q.</i>\n"

    await message.answer(
        f"👋 Salom, <b>{user.first_name}</b>!\n\n"
        "Men test javoblarini tekshiraman.\n\n"
        "<b>Yuborish formati:</b>\n"
        "  <code>TEST_KODI javoblaringiz</code>\n"
        "  Masalan: <code>MATH1 abcdabccab</code>\n"
        f"{tests_section}\n"
        "<b>Buyruqlar:</b>\n"
        "  /top <code>KOD</code> — Reyting\n"
        "  /mystats — Sizning statistika\n"
        "  /help — Yordam",
        parse_mode="HTML",
    )


# ─── /help ───────────────────────────────────
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    tests = await get_all_tests()
    if tests:
        test_list = "  ".join(f"<code>{t['code']}</code>" for t in tests)
    else:
        test_list = "<i>yo'q</i>"

    await message.answer(
        "📖 <b>Yordam</b>\n\n"
        "<b>Test topshirish:</b>\n"
        "  <code>TEST_KODI javoblar</code>\n"
        "  Masalan: <code>ENG1 bbacddacba</code>\n\n"
        f"<b>Testlar:</b> {test_list}\n\n"
        "<b>Buyruqlar:</b>\n"
        "  /top <code>KOD</code> — Top 10 reyting\n"
        "  /mystats — Sizning natijalaringiz\n"
        "  /help — Shu menyu",
        parse_mode="HTML",
    )


# ─── /mystats ────────────────────────────────
@router.message(Command("mystats"))
async def cmd_mystats(message: Message) -> None:
    user = message.from_user
    await get_or_create_user(user.id, user.full_name or "Anonim")

    stats = await get_user_stats(user.id)
    if not stats:
        await message.answer(
            "📭 Siz hali test topshirmagansiz.\n"
            "<code>TEST_KODI javoblar</code> yuboring!",
            parse_mode="HTML",
        )
        return

    history = await get_user_history(user.id, limit=5)

    hist_lines = []
    for h in history:
        pct = round(h["score"] / h["total"] * 100)
        date = h["created_at"][:10]
        hist_lines.append(
            f"  • {h['test_code']}: {h['score']}/{h['total']} ({pct}%) — {date}"
        )

    hist_text = "\n".join(hist_lines) if hist_lines else "  —"

    await message.answer(
        f"📊 <b>{user.first_name} — statistika</b>\n\n"
        f"Jami urinishlar: <b>{stats['attempts']}</b>\n"
        f"Eng yaxshi natija: <b>{stats['best_score']}/{stats['best_total']}</b> "
        f"({stats['best_pct']}%) — {stats['best_test']}\n"
        f"O'rtacha: <b>{stats['avg_pct']}%</b>\n\n"
        f"<b>So'nggi urinishlar:</b>\n{hist_text}",
        parse_mode="HTML",
    )


# ─── /top ────────────────────────────────────
@router.message(Command("top"))
async def cmd_top(message: Message, command: CommandObject) -> None:
    arg = (command.args or "").strip().upper()

    if not arg:
        tests = await get_all_tests()
        if not tests:
            await message.answer("Hozircha testlar yo'q.")
            return
        lines = ["📋 Test kodini kiriting:\n"]
        for t in tests:
            lines.append(f"  /top <code>{t['code']}</code>")
        await message.answer("\n".join(lines), parse_mode="HTML")
        return

    rows = await get_leaderboard(arg, limit=10)
    if not rows:
        await message.answer(
            f"<b>{arg}</b> bo'yicha hali natijalar yo'q.",
            parse_mode="HTML",
        )
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = [f"🏆 <b>TOP 10 — {arg}</b>\n"]
    for i, r in enumerate(rows, 1):
        medal = medals.get(i, f"{i}.")
        pct = round(r["score"] / r["total"] * 100)
        lines.append(
            f"{medal} {r['name']} — {r['score']}/{r['total']} ({pct}%)"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")
