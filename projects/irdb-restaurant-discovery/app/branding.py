"""Shared helpers for collapsing messy branch names into one canonical brand."""

import re
import unicodedata

from sqlalchemy import case, func


BRAND_ALIAS_RULES = [
    ("zizzi ristorante", "zizzi", "Zizzi"),
    ("starbucks coffee", "starbucks", "Starbucks"),
    ("avonmeads starbucks", "starbucks", "Starbucks"),
    ("subway fishponds", "subway", "Subway"),
    ("subway winterstoke", "subway", "Subway"),
    ("rontec st andrews plus subway", "subway", "Subway"),
    ("rontec st andrews subway", "subway", "Subway"),
    ("root and ember", "root", "Root"),
    ("roots independent street team", "root", "Root"),
    ("honest burgers", "honest burger", "Honest Burger"),
    ("dominos pizza", "domino s pizza", "Domino's Pizza"),
    ("nando s chickenland limited", "nandos", "Nandos"),
    ("miller and carter steakhouse and restaurant", "miller and carter", "Miller & Carter"),
    ("miller and carter steakhouse restaurant", "miller and carter", "Miller & Carter"),
    ("yakinori noodle bento and sushi restaurant", "yakinori", "Yakinori"),
    ("caffe nero", "caffe nero", "Caffe Nero"),
]


def slugify_brand_name(value: str | None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    return slug.strip("-")


def normalize_brand_value(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", (value or "").strip().lower())
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.replace("&", " and ")
    normalized = normalized.replace("+", " plus ")
    for char in ("'", ".", ",", "-", "(", ")"):
        normalized = normalized.replace(char, " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def canonical_brand_key(value: str | None) -> str:
    normalized = normalize_brand_value(value)
    for alias, canonical, _display_name in BRAND_ALIAS_RULES:
        if normalized == alias:
            return canonical
    if normalized.startswith("kfc "):
        return "kfc"
    if normalized.startswith("las iguanas "):
        return "las iguanas"
    if normalized.startswith("papa john "):
        return "papa johns"
    if normalized.startswith("yakinori "):
        return "yakinori"
    return normalized


def canonical_brand_display_name(value: str | None) -> str:
    normalized = normalize_brand_value(value)
    for alias, _canonical, display_name in BRAND_ALIAS_RULES:
        if normalized == alias:
            return display_name
    if normalized.startswith("kfc "):
        return "KFC"
    if normalized.startswith("las iguanas "):
        return "Las Iguanas"
    if normalized.startswith("papa john "):
        return "Papa Johns"
    if normalized.startswith("yakinori "):
        return "Yakinori"
    return (value or "").strip()


def canonical_brand_expr(column_expr):
    normalized_expr = func.lower(func.trim(column_expr))
    normalized_expr = func.replace(normalized_expr, "&", " and ")
    normalized_expr = func.replace(normalized_expr, "+", " plus ")
    for char in ("'", ".", ",", "-", "(", ")"):
        normalized_expr = func.replace(normalized_expr, char, " ")
    normalized_expr = func.trim(normalized_expr)
    normalized_expr = func.replace(normalized_expr, "  ", " ")
    normalized_expr = func.replace(normalized_expr, "  ", " ")

    return case(
        (normalized_expr == "zizzi ristorante", "zizzi"),
        (normalized_expr == "starbucks coffee", "starbucks"),
        (normalized_expr == "avonmeads starbucks", "starbucks"),
        (normalized_expr == "subway fishponds", "subway"),
        (normalized_expr == "subway winterstoke", "subway"),
        (normalized_expr == "rontec st andrews plus subway", "subway"),
        (normalized_expr == "rontec st andrews subway", "subway"),
        (normalized_expr == "root and ember", "root"),
        (normalized_expr == "roots independent street team", "root"),
        (normalized_expr == "honest burgers", "honest burger"),
        (normalized_expr == "dominos pizza", "domino s pizza"),
        (normalized_expr == "nando s chickenland limited", "nandos"),
        (normalized_expr == "miller and carter steakhouse and restaurant", "miller and carter"),
        (normalized_expr == "miller and carter steakhouse restaurant", "miller and carter"),
        (normalized_expr == "yakinori noodle bento and sushi restaurant", "yakinori"),
        (normalized_expr == "caffe nero", "caffe nero"),
        (normalized_expr == "caffÃ¨ nero", "caffe nero"),
        (normalized_expr.like("kfc %"), "kfc"),
        (normalized_expr.like("las iguanas %"), "las iguanas"),
        (normalized_expr.like("papa john %"), "papa johns"),
        (normalized_expr.like("yakinori %"), "yakinori"),
        else_=normalized_expr,
    )

