from app.config.settings import Settings
from app.tools.sql_validator_tool import validate_sql


def test_valid_aggregate_select_passes() -> None:
    sql = """
    SELECT b.branch_name, count(i.incident_id) AS critical_incidents
    FROM incidents i
    JOIN branches b ON i.branch_id = b.branch_id
    WHERE i.severity_level = 'critical'
    GROUP BY b.branch_name
    ORDER BY critical_incidents DESC
    LIMIT 5
    """
    result = validate_sql(sql, Settings())

    assert result.is_valid is True
    assert result.safe_sql is not None
    assert result.referenced_tables == ["branches", "incidents"]


def test_rejects_write_statement() -> None:
    result = validate_sql("DELETE FROM incidents WHERE severity_level = 'low'", Settings())

    assert result.is_valid is False
    assert any("Keyword" in reason for reason in result.reasons)


def test_rejects_multiple_statements() -> None:
    result = validate_sql("SELECT incident_id FROM incidents LIMIT 5; SELECT branch_id FROM branches", Settings())

    assert result.is_valid is False
    assert any("múltiples statements" in reason for reason in result.reasons)


def test_allows_single_trailing_semicolon_by_normalizing() -> None:
    result = validate_sql(
        """
        SELECT c.category_name, count(i.incident_id) AS total_incidentes
        FROM incidents i
        JOIN categories c ON i.category_id = c.category_id
        GROUP BY c.category_name;
        """,
        Settings(),
    )

    assert result.is_valid is True
    assert result.safe_sql is not None
    assert not result.safe_sql.endswith(";")


def test_rejects_unknown_table() -> None:
    result = validate_sql("SELECT user_id FROM users LIMIT 10", Settings())

    assert result.is_valid is False
    assert any("Tablas no permitidas" in reason for reason in result.reasons)


def test_rejects_select_star() -> None:
    result = validate_sql("SELECT * FROM incidents LIMIT 10", Settings())

    assert result.is_valid is False
    assert any("SELECT *" in reason for reason in result.reasons)
