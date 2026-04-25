"""
services/grader.py — Grading logic. DB ga tegmaydi.
"""


def normalize(text: str) -> str:
    return text.lower().replace(" ", "").strip()


def grade(key: str, user_answers: str) -> dict:
    """
    key          — to'g'ri javoblar (DB dan)
    user_answers — foydalanuvchi yuborgani

    Qaytaradi: score, total, percentage, correct_map
    """
    key_norm  = normalize(key)
    user_norm = normalize(user_answers)

    total   = len(key_norm)
    score   = 0
    correct_map: list[bool | None] = []

    for i in range(total):
        if i < len(user_norm):
            ok = user_norm[i] == key_norm[i]
            if ok:
                score += 1
            correct_map.append(ok)
        else:
            correct_map.append(None)   # javob berilmagan

    percentage = round(score / total * 100, 1) if total else 0.0

    return {
        "score":       score,
        "total":       total,
        "percentage":  percentage,
        "correct_map": correct_map,
        "user_norm":   user_norm,
    }


def parse_message(text: str) -> tuple[str, str] | None:
    """
    'TEST_CODE javoblar'  →  (TEST_CODE, javoblar)
    Noto'g'ri format  →  None
    """
    parts = text.strip().split(None, 1)
    if len(parts) != 2:
        return None
    code, answers = parts
    if not code.replace("_", "").isalnum():
        return None
    return code.upper(), answers
