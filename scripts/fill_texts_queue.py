#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Автозаполнение порций текстов через GPT 5.2 (OpenAI API).

Как работает:
- Очередь порций хранится в SQLite: /opt/natal_chart/data/texts.db, таблица fill_queue
- Скрипт берёт 1 следующую порцию (status=pending), делает запрос к модели, ждёт СТРОГО JSON-массив
- Записывает тексты в нужную таблицу и помечает порцию done

ENV:
- OPENAI_API_KEY (обязательно)
- OPENAI_MODEL (по умолчанию: gpt-5.2)
- OPENAI_API_URL (по умолчанию: https://api.openai.com/v1/chat/completions)

Запуск:
- 1 порция:   python3 scripts/fill_texts_queue.py --once
- цикл:       python3 scripts/fill_texts_queue.py --loop
- dry-run:    python3 scripts/fill_texts_queue.py --once --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

# На сервере файл будет лежать в /opt/natal_chart/scripts/
# Поэтому parents[1] укажет на /opt/natal_chart/
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "texts.db"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2").strip()
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions").strip()

PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
SIGNS_RU = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
ASPECTS = ["Conjunction", "Opposition", "Trine", "Square", "Sextile", "Quincunx"]
HOUSES = list(range(1, 13))

ASPECTS_RU = {
    "Conjunction": "Соединение",
    "Opposition": "Оппозиция",
    "Trine": "Тригон",
    "Square": "Квадрат",
    "Sextile": "Секстиль",
    "Quincunx": "Квинконс",
}

SYSTEM_PROMPT = (
    "Ты — профессиональный астролог-практик с 20-летним опытом. "
    "Пиши уникальные, конкретные, практичные интерпретации без воды. "
    "Не повторяйся."
)

RULES_PROMPT = """Требования к каждому тексту:
- 150–250 слов
- Начни с ключевой мысли
- Дай 2–3 конкретных проявления
- Заверши практическим советом/ориентиром
- Контекст важен: натал (характер), транзит (сейчас), соляр (в этом году), лунар (в этом месяце), синастрия (между вами)
- Верни СТРОГО JSON без markdown и без комментариев
""".strip()


@dataclass(frozen=True)
class Portion:
    code: str
    title: str
    table: str
    text_col: str
    key_cols: Tuple[str, ...]
    context: str
    selector: Dict[str, Any]


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_queue_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fill_queue (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            table_name TEXT NOT NULL,
            text_col TEXT NOT NULL,
            key_cols TEXT NOT NULL,
            context TEXT NOT NULL,
            selector_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            started_at INTEGER,
            finished_at INTEGER,
            last_error TEXT,
            last_response_json TEXT
        )
        """
    )
    conn.commit()


def portion_definitions() -> List[Portion]:
    portions: List[Portion] = []

    # A1-A3
    portions.append(
        Portion(
            code="A1",
            title="Синастрия: уровни совместимости (6)",
            table="synastry_levels",
            text_col="description",
            key_cols=("level",),
            context="synastry_levels",
            selector={"levels": ["ideal", "excellent", "good", "average", "difficult", "very_difficult"]},
        )
    )
    portions.append(
        Portion(
            code="A2",
            title="Синастрия: рекомендации (15)",
            table="synastry_recommendations",
            text_col="recommendation",
            key_cols=("category", "condition"),
            context="synastry_recommendations",
            selector={},
        )
    )
    portions.append(
        Portion(
            code="A3",
            title="Синастрия: сферы (25)",
            table="synastry_spheres",
            text_col="text",
            key_cols=("sphere", "level"),
            context="synastry_spheres",
            selector={},
        )
    )

    # Натал аспекты: B1..B15 (как в гайде)
    def add_pair_block(code: str, pairs: Sequence[Tuple[str, str]]) -> None:
        portions.append(
            Portion(
                code=code,
                title="Натал: аспекты " + ", ".join([f"{a}-{b}" for a, b in pairs]),
                table="natal_aspects",
                text_col="text",
                key_cols=("planet1", "planet2", "aspect"),
                context="natal_aspects",
                selector={"pairs": list(pairs), "aspects": ASPECTS},
            )
        )

    add_pair_block("B1", [("Sun", "Moon"), ("Sun", "Mercury")])
    add_pair_block("B2", [("Sun", "Venus"), ("Sun", "Mars")])
    add_pair_block("B3", [("Sun", "Jupiter"), ("Sun", "Saturn")])
    add_pair_block("B4", [("Sun", "Uranus"), ("Sun", "Neptune"), ("Sun", "Pluto")])
    add_pair_block("B5", [("Moon", "Mercury"), ("Moon", "Venus")])
    add_pair_block("B6", [("Moon", "Mars"), ("Moon", "Jupiter")])
    add_pair_block("B7", [("Moon", "Saturn"), ("Moon", "Uranus")])
    add_pair_block("B8", [("Moon", "Neptune"), ("Moon", "Pluto")])
    add_pair_block("B9", [("Mercury", "Venus"), ("Mercury", "Mars"), ("Mercury", "Jupiter")])
    add_pair_block("B10", [("Mercury", "Saturn"), ("Mercury", "Uranus"), ("Mercury", "Neptune"), ("Mercury", "Pluto")])
    add_pair_block("B11a", [("Venus", "Mars"), ("Venus", "Jupiter"), ("Venus", "Saturn")])
    add_pair_block("B11b", [("Venus", "Uranus"), ("Venus", "Neptune"), ("Venus", "Pluto")])
    add_pair_block("B12", [("Mars", "Jupiter"), ("Mars", "Saturn"), ("Mars", "Uranus"), ("Mars", "Neptune"), ("Mars", "Pluto")])
    add_pair_block("B13", [("Jupiter", "Saturn"), ("Jupiter", "Uranus"), ("Jupiter", "Neptune"), ("Jupiter", "Pluto")])
    add_pair_block("B14", [("Saturn", "Uranus"), ("Saturn", "Neptune"), ("Saturn", "Pluto"), ("Uranus", "Neptune")])
    add_pair_block("B15", [("Uranus", "Pluto"), ("Neptune", "Pluto")])

    # Транзит: планеты в домах (C1..C5)
    for code, pls in [
        ("C1", ["Sun", "Moon"]),
        ("C2", ["Mercury", "Venus"]),
        ("C3", ["Mars", "Jupiter"]),
        ("C4", ["Saturn", "Uranus"]),
        ("C5", ["Neptune", "Pluto"]),
    ]:
        portions.append(
            Portion(
                code=code,
                title=f"Транзиты: планеты в домах {', '.join(pls)}",
                table="transit_planets_houses",
                text_col="text",
                key_cols=("planet", "house"),
                context="transit_planets_houses",
                selector={"planets": pls, "houses": HOUSES},
            )
        )

    # Чанки натальных планет для аспектов (4+4+2) = 30 порций на 10 планет
    chunks = [
        ["Sun", "Moon", "Mercury", "Venus"],
        ["Mars", "Jupiter", "Saturn", "Uranus"],
        ["Neptune", "Pluto"],
    ]

    # Транзит: аспекты к наталу (D1..D30)
    d = 1
    for tp in PLANETS:
        for chunk in chunks:
            portions.append(
                Portion(
                    code=f"D{d}",
                    title=f"Транзиты: {tp} к наталу",
                    table="transit_aspects",
                    text_col="text",
                    key_cols=("transit_planet", "natal_planet", "aspect"),
                    context="transit_aspects",
                    selector={"transit_planet": tp, "natal_planets": chunk, "aspects": ASPECTS},
                )
            )
            d += 1

    # Соляр/Лунар: планеты в знаках/домах (E,F,H,I)
    def add_sign(prefix: str, table: str, title: str) -> None:
        for idx, pls in [(1,["Sun","Moon"]),(2,["Mercury","Venus"]),(3,["Mars","Jupiter"]),(4,["Saturn","Uranus"]),(5,["Neptune","Pluto"])]:
            portions.append(
                Portion(
                    code=f"{prefix}{idx}",
                    title=f"{title}: планеты в знаках {', '.join(pls)}",
                    table=table,
                    text_col="text",
                    key_cols=("planet", "sign"),
                    context=table,
                    selector={"planets": pls, "signs": SIGNS_RU},
                )
            )

    def add_house(prefix: str, table: str, title: str) -> None:
        for idx, pls in [(1,["Sun","Moon"]),(2,["Mercury","Venus"]),(3,["Mars","Jupiter"]),(4,["Saturn","Uranus"]),(5,["Neptune","Pluto"])]:
            portions.append(
                Portion(
                    code=f"{prefix}{idx}",
                    title=f"{title}: планеты в домах {', '.join(pls)}",
                    table=table,
                    text_col="text",
                    key_cols=("planet", "house"),
                    context=table,
                    selector={"planets": pls, "houses": HOUSES},
                )
            )

    add_sign("E", "solar_planets_signs", "Соляр")
    add_house("F", "solar_planets_houses", "Соляр")
    add_sign("H", "lunar_planets_signs", "Лунар")
    add_house("I", "lunar_planets_houses", "Лунар")

    # Соляр/Лунар: аспекты к наталу (G/J) — тоже 30 порций
    def add_cross(prefix: str, table: str, outer_col: str, title: str) -> None:
        n = 1
        for op in PLANETS:
            for chunk in chunks:
                portions.append(
                    Portion(
                        code=f"{prefix}{n}",
                        title=f"{title}: {op} к наталу",
                        table=table,
                        text_col="text",
                        key_cols=(outer_col, "natal_planet", "aspect"),
                        context=table,
                        selector={outer_col: op, "natal_planets": chunk, "aspects": ASPECTS},
                    )
                )
                n += 1

    add_cross("G", "solar_aspects", "solar_planet", "Соляр")
    add_cross("J", "lunar_aspects", "lunar_planet", "Лунар")

    # Синастрия: аспекты (K1..K30)
    k = 1
    for p1 in PLANETS:
        for chunk in chunks:
            portions.append(
                Portion(
                    code=f"K{k}",
                    title=f"Синастрия: {p1} к планетам партнёра",
                    table="synastry_aspects",
                    text_col="text",
                    key_cols=("planet1", "planet2", "aspect"),
                    context="synastry_aspects",
                    selector={"planet1": p1, "planet2_list": chunk, "aspects": ASPECTS},
                )
            )
            k += 1

    # Синастрия: планеты в домах партнёра (L1..L5)
    for code, pls in [
        ("L1", ["Sun", "Moon"]),
        ("L2", ["Mercury", "Venus"]),
        ("L3", ["Mars", "Jupiter"]),
        ("L4", ["Saturn", "Uranus"]),
        ("L5", ["Neptune", "Pluto"]),
    ]:
        portions.append(
            Portion(
                code=code,
                title=f"Синастрия: планеты в домах партнёра {', '.join(pls)}",
                table="synastry_planets_houses",
                text_col="text",
                key_cols=("planet", "house"),
                context="synastry_planets_houses",
                selector={"planets": pls, "houses": HOUSES},
            )
        )

    return portions


def seed_queue(conn: sqlite3.Connection) -> None:
    ensure_queue_schema(conn)
    count = conn.execute("SELECT COUNT(*) FROM fill_queue").fetchone()[0]
    if count and int(count) > 0:
        return

    now = int(time.time())
    for p in portion_definitions():
        conn.execute(
            """
            INSERT OR IGNORE INTO fill_queue
            (code, title, table_name, text_col, key_cols, context, selector_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                p.code,
                p.title,
                p.table,
                p.text_col,
                json.dumps(list(p.key_cols), ensure_ascii=False),
                p.context,
                json.dumps(p.selector, ensure_ascii=False),
                now,
            ),
        )
    conn.commit()


def fetch_next(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM fill_queue WHERE status='pending' ORDER BY id ASC LIMIT 1").fetchone()


def mark_started(conn: sqlite3.Connection, qid: int) -> None:
    conn.execute(
        "UPDATE fill_queue SET status='running', started_at=?, last_error=NULL WHERE id=?",
        (int(time.time()), qid),
    )
    conn.commit()


def mark_done(conn: sqlite3.Connection, qid: int, response_text: str) -> None:
    conn.execute(
        "UPDATE fill_queue SET status='done', finished_at=?, last_response_json=? WHERE id=?",
        (int(time.time()), response_text[:200000], qid),
    )
    conn.commit()


def mark_error(conn: sqlite3.Connection, qid: int, err: str) -> None:
    conn.execute(
        "UPDATE fill_queue SET status='pending', last_error=? WHERE id=?",
        (err[:2000], qid),
    )
    conn.commit()


def _in_clause(values: Sequence[Any]) -> Tuple[str, List[Any]]:
    placeholders = ",".join(["?"] * len(values))
    return f"({placeholders})", list(values)


def select_items(conn: sqlite3.Connection, table: str, text_col: str, key_cols: Sequence[str], selector: Dict[str, Any]) -> List[Dict[str, Any]]:
    where = f"({text_col} IS NULL OR length({text_col}) <= 10)"
    params: List[Any] = []

    if table == "natal_aspects":
        pairs = selector["pairs"]
        aspects = selector["aspects"]
        pair_sql = []
        for p1, p2 in pairs:
            pair_sql.append("(planet1=? AND planet2=?)")
            params.extend([p1, p2])
        where += " AND (" + " OR ".join(pair_sql) + ")"
        in_sql, in_params = _in_clause(aspects)
        where += f" AND aspect IN {in_sql}"
        params.extend(in_params)

    elif table == "transit_aspects":
        where += " AND transit_planet=?"
        params.append(selector["transit_planet"])
        in_sql, in_params = _in_clause(selector["natal_planets"])
        where += f" AND natal_planet IN {in_sql}"
        params.extend(in_params)
        in_sql, in_params = _in_clause(selector["aspects"])
        where += f" AND aspect IN {in_sql}"
        params.extend(in_params)

    elif table == "solar_aspects":
        where += " AND solar_planet=?"
        params.append(selector["solar_planet"])
        in_sql, in_params = _in_clause(selector["natal_planets"])
        where += f" AND natal_planet IN {in_sql}"
        params.extend(in_params)
        in_sql, in_params = _in_clause(selector["aspects"])
        where += f" AND aspect IN {in_sql}"
        params.extend(in_params)

    elif table == "lunar_aspects":
        where += " AND lunar_planet=?"
        params.append(selector["lunar_planet"])
        in_sql, in_params = _in_clause(selector["natal_planets"])
        where += f" AND natal_planet IN {in_sql}"
        params.extend(in_params)
        in_sql, in_params = _in_clause(selector["aspects"])
        where += f" AND aspect IN {in_sql}"
        params.extend(in_params)

    elif table == "synastry_aspects":
        where += " AND planet1=?"
        params.append(selector["planet1"])
        in_sql, in_params = _in_clause(selector["planet2_list"])
        where += f" AND planet2 IN {in_sql}"
        params.extend(in_params)
        in_sql, in_params = _in_clause(selector["aspects"])
        where += f" AND aspect IN {in_sql}"
        params.extend(in_params)

    elif table in ("transit_planets_houses", "solar_planets_houses", "lunar_planets_houses", "synastry_planets_houses"):
        in_sql, in_params = _in_clause(selector["planets"])
        where += f" AND planet IN {in_sql}"
        params.extend(in_params)
        in_sql, in_params = _in_clause(selector["houses"])
        where += f" AND house IN {in_sql}"
        params.extend(in_params)

    elif table in ("solar_planets_signs", "lunar_planets_signs"):
        in_sql, in_params = _in_clause(selector["planets"])
        where += f" AND planet IN {in_sql}"
        params.extend(in_params)
        in_sql, in_params = _in_clause(selector["signs"])
        where += f" AND sign IN {in_sql}"
        params.extend(in_params)

    elif table == "synastry_levels":
        in_sql, in_params = _in_clause(selector["levels"])
        where += f" AND level IN {in_sql}"
        params.extend(in_params)

    cols = ", ".join(key_cols)
    sql = f"SELECT {cols} FROM {table} WHERE {where} ORDER BY id ASC"
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def context_line(context_key: str) -> str:
    if context_key == "natal_aspects":
        return "Контекст: НАТАЛ (черты личности и устойчивые паттерны)."
    if context_key == "transit_aspects":
        return "Контекст: ТРАНЗИТЫ (сейчас/в ближайшие недели)."
    if context_key == "solar_aspects":
        return "Контекст: СОЛЯР (в этом году)."
    if context_key == "lunar_aspects":
        return "Контекст: ЛУНАР (в этом месяце)."
    if context_key == "synastry_aspects":
        return "Контекст: СИНАСТРИЯ (между вами/в отношениях)."
    if context_key == "solar_planets_signs":
        return "Контекст: СОЛЯР (в этом году — планета в знаке)."
    if context_key == "lunar_planets_signs":
        return "Контекст: ЛУНАР (в этом месяце — планета в знаке)."
    if context_key == "transit_planets_houses":
        return "Контекст: ТРАНЗИТЫ (планета проходит по натальному дому сейчас)."
    if context_key == "synastry_levels":
        return "Контекст: СИНАСТРИЯ (общий уровень пары)."
    if context_key == "synastry_spheres":
        return "Контекст: СИНАСТРИЯ (сферы отношений)."
    if context_key == "synastry_recommendations":
        return "Контекст: СИНАСТРИЯ (рекомендации/советы)."
    return f"Контекст: {context_key}."


def build_prompt(portion: sqlite3.Row, items: List[Dict[str, Any]]) -> Tuple[str, str]:
    system = SYSTEM_PROMPT + "\n\n" + RULES_PROMPT
    user = f"""
ЗАДАНИЕ {portion['code']}: {portion['title']}
{context_line(portion['context'])}

Справочник аспектов (EN->RU): {json.dumps(ASPECTS_RU, ensure_ascii=False)}
Планеты: {', '.join(PLANETS)}
Знаки (RU): {', '.join(SIGNS_RU)}

Сгенерируй {len(items)} текстов.
Верни СТРОГО JSON массив объектов.
Каждый объект должен содержать ВСЕ ключи из входного списка + поле "text".

Входной список объектов (нужно заполнить поле text):
{json.dumps(items, ensure_ascii=False)}
""".strip()
    return system, user


def call_openai(system: str, user: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY не задан")

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
    }

    resp = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def extract_json_array(text: str) -> List[Dict[str, Any]]:
    s = (text or "").strip()
    start = s.find("[")
    end = s.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Не найден JSON-массив в ответе")
    raw = s[start : end + 1]
    arr = json.loads(raw)
    if not isinstance(arr, list):
        raise ValueError("Ответ не JSON-массив")
    for obj in arr:
        if not isinstance(obj, dict):
            raise ValueError("В массиве есть не-объект")
    return arr


def apply_updates(conn: sqlite3.Connection, table: str, text_col: str, key_cols: Sequence[str], rows: List[Dict[str, Any]]) -> int:
    updated = 0
    for obj in rows:
        text = (obj.get("text") or "").strip()
        if len(text) <= 10:
            continue
        where = " AND ".join([f"{c}=?" for c in key_cols])
        sql = f"UPDATE {table} SET {text_col}=? WHERE {where}"
        params = [text] + [obj.get(c) for c in key_cols]
        cur = conn.execute(sql, params)
        updated += cur.rowcount
    conn.commit()
    return updated


def run_once(dry_run: bool = False) -> int:
    conn = connect_db()
    try:
        ensure_queue_schema(conn)
        seed_queue(conn)
        row = fetch_next(conn)
        if not row:
            print("Очередь пустая: все порции выполнены")
            return 0

        qid = int(row["id"])
        mark_started(conn, qid)

        key_cols = json.loads(row["key_cols"])
        selector = json.loads(row["selector_json"])
        items = select_items(conn, row["table_name"], row["text_col"], key_cols, selector)

        if not items:
            mark_done(conn, qid, json.dumps({"skipped": True, "reason": "no empty items"}, ensure_ascii=False))
            print(f"{row['code']}: нечего заполнять — DONE")
            return 1

        system, user = build_prompt(row, items)
        print(f"\n=== NEXT: {row['code']} | {row['title']} ===")
        print(f"Table: {row['table_name']} | Items: {len(items)}")

        if dry_run:
            print("\n--- PROMPT (начало) ---\n" + user[:2000])
            mark_done(conn, qid, json.dumps({"dry_run": True}, ensure_ascii=False))
            print(f"{row['code']}: DRY-RUN DONE")
            return 1

        raw = call_openai(system, user)
        arr = extract_json_array(raw)

        # валидация ключей
        for obj in arr:
            for c in key_cols:
                if c not in obj:
                    raise ValueError(f"В ответе нет ключа {c}")

        updated = apply_updates(conn, row["table_name"], row["text_col"], key_cols, arr)
        mark_done(conn, qid, raw)
        print(f"{row['code']}: DONE, updated={updated}")
        return 1

    except Exception as e:
        try:
            if "qid" in locals():
                mark_error(conn, int(locals()["qid"]), str(e))
        except Exception:
            pass
        print(f"ERROR: {e}")
        return 2
    finally:
        conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--sleep", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.once and not args.loop:
        args.once = True

    if args.once:
        raise SystemExit(run_once(dry_run=args.dry_run))

    while True:
        rc = run_once(dry_run=args.dry_run)
        if rc == 0:
            break
        time.sleep(max(1, args.sleep))


if __name__ == "__main__":
    main()
