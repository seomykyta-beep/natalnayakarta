# DB-backed тексты (texts.db) с fallback на JSON

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TEXTS_DIR = BASE_DIR / "texts"
if not TEXTS_DIR.exists():
    TEXTS_DIR = BASE_DIR / "data" / "texts"

DB_PATH = BASE_DIR / "data" / "texts.db"

_CONN = None


def _db():
    global _CONN
    if _CONN is None:
        if not DB_PATH.exists():
            return None
        _CONN = sqlite3.connect(str(DB_PATH))
        _CONN.row_factory = sqlite3.Row
    return _CONN


def load_json(filename):
    path = TEXTS_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# JSON fallback (если DB нет)
PLANETS_IN_SIGNS = load_json("planets_in_signs.json")
PLANETS_IN_HOUSES = load_json("planets_in_houses.json")
ASPECTS = load_json("aspects.json")

ELEMENTS = load_json("elements.json")
PLANETS = load_json("planets.json")
HOUSES = load_json("houses.json")
DIGNITIES = load_json("dignities.json")

DEGREES_ALL = load_json("degrees_all.json")
DEGREES_ROYAL = load_json("degrees_royal.json")
DEGREES_DESTRUCTIVE = load_json("degrees_destructive.json")

TEXTS = {
    "signs": PLANETS_IN_SIGNS,
    "houses": PLANETS_IN_HOUSES,
    "aspects": ASPECTS,
}


def _parse_house(sub_key):
    if sub_key is None:
        return None
    if isinstance(sub_key, int):
        return sub_key
    s = str(sub_key)
    if s.startswith("House"):
        s = s.replace("House", "")
    try:
        return int(s)
    except Exception:
        return None


def get_text(category, planet_key, sub_key=None, gender="general", mode="natal"):
    con = _db()
    if con is None:
        # JSON fallback
        if category == "signs":
            key = f"{planet_key}_{sub_key}" if sub_key else planet_key
            data = PLANETS_IN_SIGNS.get(key, {})
            if isinstance(data, dict):
                return data.get(gender) or data.get("general", "")
            return str(data) if data else ""
        if category == "houses":
            key = f"{planet_key}_{sub_key}" if sub_key else planet_key
            data = PLANETS_IN_HOUSES.get(key, {})
            if isinstance(data, dict):
                return data.get(gender) or data.get("general", "")
            return str(data) if data else ""
        if category == "aspects":
            return ASPECTS.get(planet_key, {})
        return ""

    if category == "houses":
        house = _parse_house(sub_key)
        if house is None:
            return ""
        table_by_mode = {
            "natal": "natal_planets_houses",
            "solar": "solar_planets_houses",
            "lunar": "lunar_planets_houses",
        }
        table = table_by_mode.get(mode)
        if not table:
            return ""
        cur = con.cursor()
        cur.execute(f"SELECT text FROM {table} WHERE planet=? AND house=?", (planet_key, house))
        row = cur.fetchone()
        return (row["text"] if row else "") or ""

    if category == "signs":
        if not sub_key:
            return ""
        table_by_mode = {
            "natal": "natal_planets_signs",
            "solar": "solar_planets_signs",
            "lunar": "lunar_planets_signs",
        }
        table = table_by_mode.get(mode)
        if not table:
            return ""
        cur = con.cursor()
        cur.execute(f"SELECT text FROM {table} WHERE planet=? AND sign=?", (planet_key, sub_key))
        row = cur.fetchone()
        return (row["text"] if row else "") or ""

    if category == "aspects":
        return {}

    return ""


def get_interpretation(planet_key, sign=None, gender="general", mode="natal"):
    if not sign:
        return ""
    return get_text("signs", planet_key, sign, gender=gender, mode=mode)


def get_db_aspect_text(planet1, planet2, aspect_type, mode="natal", outer_planet=None, natal_planet=None):
    con = _db()
    if con is None:
        key = f"{planet1}_{planet2}"
        rev = f"{planet2}_{planet1}"
        data = ASPECTS.get(key) or ASPECTS.get(rev) or {}
        if isinstance(data, dict):
            return data.get(aspect_type, "") or ""
        return ""

    cur = con.cursor()

    if mode == "natal":
        cur.execute("SELECT text FROM natal_aspects WHERE planet1=? AND planet2=? AND aspect=?", (planet1, planet2, aspect_type))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT text FROM natal_aspects WHERE planet1=? AND planet2=? AND aspect=?", (planet2, planet1, aspect_type))
            row = cur.fetchone()
        return (row["text"] if row else "") or ""

    op = outer_planet or planet1
    np = natal_planet or planet2

    if mode == "transit":
        cur.execute("SELECT text FROM transit_aspects WHERE transit_planet=? AND natal_planet=? AND aspect=?", (op, np, aspect_type))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT text FROM transit_aspects WHERE transit_planet=? AND natal_planet=? AND aspect=?", (np, op, aspect_type))
            row = cur.fetchone()
        return (row["text"] if row else "") or ""

    if mode == "solar":
        cur.execute("SELECT text FROM solar_aspects WHERE solar_planet=? AND natal_planet=? AND aspect=?", (op, np, aspect_type))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT text FROM solar_aspects WHERE solar_planet=? AND natal_planet=? AND aspect=?", (np, op, aspect_type))
            row = cur.fetchone()
        return (row["text"] if row else "") or ""

    if mode == "lunar":
        cur.execute("SELECT text FROM lunar_aspects WHERE lunar_planet=? AND natal_planet=? AND aspect=?", (op, np, aspect_type))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT text FROM lunar_aspects WHERE lunar_planet=? AND natal_planet=? AND aspect=?", (np, op, aspect_type))
            row = cur.fetchone()
        return (row["text"] if row else "") or ""

    if mode == "synastry":
        cur.execute("SELECT text FROM synastry_aspects WHERE planet1=? AND planet2=? AND aspect=?", (op, np, aspect_type))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT text FROM synastry_aspects WHERE planet1=? AND planet2=? AND aspect=?", (np, op, aspect_type))
            row = cur.fetchone()
        return (row["text"] if row else "") or ""

    return ""


def get_transit_house_text(planet_key, house_num):
    """Get text for transit planet in natal house"""
    con = _db()
    if con is None:
        return ""
    cur = con.cursor()
    cur.execute("SELECT text FROM transit_planets_houses WHERE planet=? AND house=?", (planet_key, house_num))
    row = cur.fetchone()
    return (row["text"] if row else "") or ""


def get_aspect_text(planet1, planet2, aspect_type, mode="natal"):
    return get_db_aspect_text(planet1, planet2, aspect_type, mode=mode)


def get_planet_info(planet_key):
    return PLANETS.get(planet_key, {})


def get_house_info(house_num):
    return HOUSES.get(str(house_num), {})


def get_element_info(element):
    return ELEMENTS.get(element, {})


def get_degree_info(abs_degree):
    deg = str(int(abs_degree) + 1)
    if deg in DEGREES_ROYAL:
        return {"type": "royal", **DEGREES_ROYAL[deg]}
    if deg in DEGREES_DESTRUCTIVE:
        return {"type": "destructive", **DEGREES_DESTRUCTIVE[deg]}
    return DEGREES_ALL.get(deg, {})


def is_royal_degree(abs_degree):
    return str(int(abs_degree) + 1) in DEGREES_ROYAL


def is_destructive_degree(abs_degree):
    return str(int(abs_degree) + 1) in DEGREES_DESTRUCTIVE
