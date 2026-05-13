from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class UserRequest(BaseModel):
    question: str = Field(min_length=3)


class ToolError(BaseModel):
    tool_name: str
    message: str
    recoverable: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class SchemaInfo(BaseModel):
    allowed_tables: list[str]
    description: str
    columns_by_table: dict[str, list[str]]
    column_descriptions: dict[str, dict[str, str]] = Field(default_factory=dict)
    relationships: list[str]


IntentType = Literal["analytical_query", "comparative_analysis", "analytical_query_with_chart"]


class ClassificationResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    method: Literal["heuristic", "llm"]
    reason: str


class SQLGenerationResult(BaseModel):
    sql: str
    rationale: str
    assumptions: list[str] = Field(default_factory=list)
    needs_chart: bool = False
    chart_type: Optional[Literal["bar", "line", "pie"]] = None

    @field_validator("assumptions", mode="before")
    @classmethod
    def coerce_assumptions(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [value]
        return value

    @field_validator("chart_type", mode="before")
    @classmethod
    def coerce_chart_type(cls, value):
        if value in {"", None, "none", "null"}:
            return None
        return value


class SQLValidationResult(BaseModel):
    is_valid: bool
    safe_sql: Optional[str] = None
    reasons: list[str] = Field(default_factory=list)
    referenced_tables: list[str] = Field(default_factory=list)


class SQLRunResult(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool = False


class AnalysisResult(BaseModel):
    executive_summary: str
    key_findings: list[str]
    caveats: list[str] = Field(default_factory=list)

    @field_validator("key_findings", "caveats", mode="before")
    @classmethod
    def coerce_text_list(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [value]
        return value


class ChartResult(BaseModel):
    chart_path: Optional[str] = None
    chart_type: Optional[str] = None
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    truncated_for_chart: bool = False
    message: str


class FinalResponse(BaseModel):
    question: str
    sql: Optional[str] = None
    summary: str
    findings: list[str] = Field(default_factory=list)
    chart_path: Optional[str] = None
    errors: list[ToolError] = Field(default_factory=list)


class AgentState(BaseModel):
    question: str
    intent: Optional[IntentType] = None
    classification: Optional[ClassificationResult] = None
    steps_taken: list[str] = Field(default_factory=list)
    tool_call_counts: dict[str, int] = Field(default_factory=dict)
    repeated_action_detected: bool = False
    schema_info: Optional[SchemaInfo] = None
    generated_sql: Optional[SQLGenerationResult] = None
    validation: Optional[SQLValidationResult] = None
    sql_result: Optional[SQLRunResult] = None
    analysis: Optional[AnalysisResult] = None
    chart: Optional[ChartResult] = None
    final_response: Optional[FinalResponse] = None
    errors: list[ToolError] = Field(default_factory=list)
