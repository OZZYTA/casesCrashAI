from app.state.models import SchemaInfo


ALLOWED_TABLES = ["branches", "categories", "incidents"]


def get_schema_info() -> SchemaInfo:
    """Return the governed schema contract exposed to the agent."""
    return SchemaInfo(
        allowed_tables=ALLOWED_TABLES,
        columns_by_table={
            "branches": ["branch_id", "branch_code", "branch_name", "city", "region", "opened_at", "is_active"],
            "categories": ["category_id", "category_name", "business_domain", "requires_followup"],
            "incidents": [
                "incident_id",
                "incident_code",
                "branch_id",
                "category_id",
                "severity_level",
                "status",
                "reported_at",
                "resolved_at",
                "affected_users",
                "resolution_hours",
                "sla_breached",
                "channel",
                "summary",
            ],
        },
        column_descriptions={
            "branches": {
                "branch_id": "Identificador numérico de la sede; llave primaria.",
                "branch_code": "Código corto operativo de la sede, útil para reportes compactos.",
                "branch_name": "Nombre legible de la sede.",
                "city": "Ciudad donde opera la sede.",
                "region": "Región comercial u operativa.",
                "opened_at": "Fecha de apertura de la sede.",
                "is_active": "Indica si la sede sigue activa.",
            },
            "categories": {
                "category_id": "Identificador numérico de la categoría; llave primaria.",
                "category_name": "Categoría funcional del incidente, por ejemplo Network, Payments o CRM.",
                "business_domain": "Dominio de negocio afectado por la categoría.",
                "requires_followup": "Indica si la categoría normalmente requiere seguimiento posterior.",
            },
            "incidents": {
                "incident_id": "Identificador numérico del incidente; llave primaria.",
                "incident_code": "Código legible del ticket/incidente.",
                "branch_id": "Llave foránea hacia branches.branch_id.",
                "category_id": "Llave foránea hacia categories.category_id.",
                "severity_level": "Severidad del incidente: low, medium, high o critical.",
                "status": "Estado del incidente: resolved u open.",
                "reported_at": "Fecha y hora en que se reportó el incidente; campo principal para filtros temporales.",
                "resolved_at": "Fecha y hora de resolución; puede ser nulo si el incidente está abierto.",
                "affected_users": "Número estimado de usuarios impactados.",
                "resolution_hours": "Horas de resolución; puede ser nulo para incidentes abiertos.",
                "sla_breached": "Indica si el incidente incumplió el SLA.",
                "channel": "Canal de reporte, por ejemplo portal, email, phone o monitoring.",
                "summary": "Descripción breve del incidente.",
            },
        },
        relationships=[
            "incidents.branch_id = branches.branch_id",
            "incidents.category_id = categories.category_id",
        ],
        description="""\
Tablas permitidas:
- branches: sedes operativas. Campos: branch_id, branch_code, branch_name, city, region,
  opened_at, is_active.
- categories: categorías de incidentes. Campos: category_id, category_name, business_domain,
  requires_followup.
- incidents: tickets/incidentes operativos. Campos: incident_id, incident_code, branch_id,
  category_id, severity_level ('low', 'medium', 'high', 'critical'), status ('resolved', 'open'),
  reported_at, resolved_at, affected_users, resolution_hours, sla_breached, channel, summary.

Relaciones:
- incidents.branch_id -> branches.branch_id
- incidents.category_id -> categories.category_id

Uso esperado:
- Agregaciones por reported_at, sede, región, categoría, dominio de negocio, severidad, estado,
  usuarios afectados, canal y brecha de SLA.
- Comparaciones mensuales/trimestrales.
- Rankings ejecutivos y distribuciones para gráficas.

Notas para SQL:
- Usa incidents.reported_at para preguntas por periodo, mes, trimestre o tendencia.
- Une incidents con branches para responder por sede, ciudad o región.
- Une incidents con categories para responder por categoría o dominio de negocio.
- Usa severity_level para filtros de severidad; no existe una columna llamada severity.
- Usa affected_users para medir impacto operativo.
- Usa sla_breached para análisis de cumplimiento.
""",
    )
