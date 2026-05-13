import re

import sqlglot
from sqlglot import exp

from app.config.settings import Settings, get_settings
from app.state.models import SQLValidationResult
from app.tools.schema_tool import ALLOWED_TABLES


FORBIDDEN_KEYWORDS = {
    "delete",
    "update",
    "insert",
    "truncate",
    "drop",
    "alter",
    "create",
    "grant",
    "revoke",
    "merge",
    "call",
    "copy",
    "execute",
}


def _normalize_sql(sql: str) -> str:
    return sql.strip().strip("`").strip()


def _strip_single_trailing_semicolon(sql: str) -> str:
    stripped = sql.rstrip()
    if stripped.endswith(";") and stripped.count(";") == 1:
        return stripped[:-1].rstrip()
    return sql


def _has_forbidden_keyword(sql: str) -> list[str]:
    lowered = sql.lower()
    return sorted([kw for kw in FORBIDDEN_KEYWORDS if re.search(rf"\b{kw}\b", lowered)])


def validate_sql(sql: str, settings: Settings | None = None) -> SQLValidationResult:
    """Validate syntax, read-only policy and table allowlist for PostgreSQL SQL."""
    settings = settings or get_settings()
    sql = _normalize_sql(sql)
    reasons: list[str] = []

    if not sql:
        return SQLValidationResult(is_valid=False, reasons=["SQL vacío."])

    sql = _strip_single_trailing_semicolon(sql)

    if ";" in sql:
        reasons.append("No se permiten puntos y coma internos ni múltiples statements.")

    forbidden = _has_forbidden_keyword(sql)
    if forbidden:
        reasons.append(f"Keyword(s) prohibidas: {', '.join(forbidden)}.")

    try:
        expressions = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        return SQLValidationResult(is_valid=False, reasons=[*reasons, f"SQL inválido: {exc}."])

    if len(expressions) != 1:
        reasons.append("La consulta debe contener exactamente una sentencia.")

    expression = expressions[0]
    if not isinstance(expression, (exp.Select, exp.Union)):
        reasons.append("La sentencia debe ser SELECT de solo lectura.")

    referenced_tables = sorted({table.name for table in expression.find_all(exp.Table)})
    disallowed_tables = sorted(set(referenced_tables) - set(ALLOWED_TABLES))
    if disallowed_tables:
        reasons.append(f"Tablas no permitidas: {', '.join(disallowed_tables)}.")

    if any(isinstance(node, exp.Star) for node in expression.walk()):
        reasons.append("No se permite SELECT *; especifica columnas necesarias.")

    lowered = sql.lower()
    if " limit " not in f" {lowered} " and not any(
        token in lowered for token in [" count(", " sum(", " avg(", " min(", " max(", " group by "]
    ):
        reasons.append(
            f"Las consultas no agregadas deben incluir LIMIT. Máximo sugerido: {settings.max_sql_rows}."
        )

    return SQLValidationResult(
        is_valid=not reasons,
        safe_sql=sql if not reasons else None,
        reasons=reasons,
        referenced_tables=referenced_tables,
    )
