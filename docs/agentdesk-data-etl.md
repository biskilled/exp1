# AgentDesk · Data ETL Solution

> A dedicated data pipeline platform built on AgentDesk, powered by **dingDONG** as the execution building blocks.

---

## Slide 1 · The Problem with Data Pipelines

Modern data teams juggle dozens of sources, formats, and delivery schedules. Traditional ETL tools require heavy configuration, offer no self-correction, and cannot explain what they did or why something failed.

**AgentDesk Data** applies the multi-agent model to the data engineering problem:

- Each stage of the pipeline is owned by a **specialised AI agent** with the right tools for its job
- Agents read metadata, detect schema drift, and adapt without manual intervention
- The full run — every extraction decision, transformation, load result — is logged and searchable
- Pipelines run on a **scheduler** (batch) or trigger on **events** (streaming)

> *"AI agents that extract, transform, and load — so your data engineers can focus on what the data means, not how to move it."*

---

## Slide 2 · The Four Agent Roles

Each role is a specialised AgentDesk agent with its own system prompt, tool set, provider, and model. Roles are wired together in a DAG pipeline and can be overridden per-run.

---

### Extractor Agent

**Job:** Connect to source systems, discover schema, and pull raw data.

**Tools available:**
- dingDONG source connectors (SQL Server, Oracle, SQLite, CSV, …)
- Schema introspection and drift detection
- Multi-threaded bulk read with configurable batch size
- Kafka consumer for event/streaming ingestion

**Output:**
```json
{
  "role": "extractor",
  "sources_read": [{"source": "crm.orders", "rows": 84200, "schema_hash": "a3f9…"}],
  "schema_changes": ["orders.discount_pct — NEW column detected"],
  "raw_payload_path": "workspace/runs/2026-05-04/extract/orders.parquet",
  "confidence": 0.97
}
```

---

### Transformer Agent

**Job:** Apply business logic, calculate derived columns, validate data quality, and reshape data to the target schema.

**Tools available:**
- dingDONG transformation engine (custom Python functions, column mapping)
- Schema propagation (auto-updates downstream targets when source changes)
- Data quality checks (nulls, ranges, referential integrity)
- Lookup and enrichment joins

**Output:**
```json
{
  "role": "transformer",
  "transformations_applied": ["normalise_currency", "join_dim_customer", "flag_late_orders"],
  "quality_issues": [{"field": "email", "issue": "3.2% null — below threshold"}],
  "output_path": "workspace/runs/2026-05-04/transform/orders_clean.parquet",
  "rows_in": 84200,
  "rows_out": 83014,
  "confidence": 0.91
}
```

---

### Loader Agent

**Job:** Write transformed data to target systems. Handles upserts, incremental loads, and full refreshes. Manages load errors and retries.

**Tools available:**
- dingDONG target connectors (SQL Server, Oracle, SQLite, data warehouse, …)
- Upsert / merge / append / full-replace strategies
- Post-load row-count and checksum validation
- Dead-letter queue for failed records

**Output:**
```json
{
  "role": "loader",
  "targets_written": [{"target": "dw.fact_orders", "rows_loaded": 83014, "strategy": "upsert"}],
  "errors": [],
  "load_duration_s": 14.3,
  "confidence": 0.99
}
```

---

### Executor Agent

**Job:** Orchestrate the full pipeline. Resolves run schedule, determines which pipelines to fire, monitors progress, retries on failure, and reports run results.

**Tools available:**
- AgentDesk pipeline scheduler (cron / interval / event trigger)
- Run dependency graph resolution
- Failure notification and retry logic
- Run history and SLA tracking

**Output:**
```json
{
  "role": "executor",
  "pipeline": "crm_to_dw_daily",
  "trigger": "cron:06:00",
  "stages_run": ["extractor", "transformer", "loader"],
  "verdict": "approved",
  "total_rows": 83014,
  "duration_s": 47.1,
  "sla_met": true
}
```

---

## Slide 3 · Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AgentDesk Data Platform                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │         Executor Agent               │
          │   Scheduler · DAG resolver           │
          │   Cron / Event trigger               │
          └──┬──────────────┬────────────────────┘
             │              │
    ┌────────▼────┐  ┌──────▼────────────────────┐
    │  BATCH      │  │  STREAMING / EVENTS        │
    │  Pipeline   │  │  Pipeline                  │
    └──────┬──────┘  └──────┬─────────────────────┘
           │                │
    ┌──────▼──────┐  ┌──────▼──────┐
    │  Extractor  │  │  Extractor  │
    │  (bulk SQL) │  │  (Kafka     │
    └──────┬──────┘  │  consumer)  │
           │         └──────┬──────┘
    ┌──────▼──────────────  │  ───────────────────┐
    │           Transformer Agent                  │
    │   dingDONG transform · quality checks        │
    └──────────────────────────┬──────────────────┘
                               │
    ┌──────────────────────────▼──────────────────┐
    │              Loader Agent                    │
    │   dingDONG connectors · upsert / append      │
    └──────┬───────────────────────────────────────┘
           │
  ┌────────▼────────────────────────────────────┐
  │           Target Systems                     │
  │   Data Warehouse · Relational DB · Files     │
  └─────────────────────────────────────────────┘

  Source Systems
  ┌──────────┐  ┌────────┐  ┌─────────┐  ┌──────┐
  │SQL Server│  │Oracle  │  │  Kafka  │  │ CSV  │
  │  MySQL   │  │SQLite  │  │ Topics  │  │Files │
  └──────────┘  └────────┘  └─────────┘  └──────┘
```

### Two execution modes

| Mode | Trigger | Use case | Source type |
|---|---|---|---|
| **Batch** | Cron schedule | Daily/hourly data loads | Relational DB, files, APIs |
| **Streaming** | Kafka event / message | Near-real-time ingestion | Kafka topics, event queues |

Both modes use the same Extractor → Transformer → Loader agent chain. Only the Extractor's tool configuration differs.

---

### dingDONG as the execution layer

[dingDONG](https://github.com/biskilled/dingDONG) provides the low-level data movement building blocks that each agent calls as tools:

| dingDONG component | Used by | What it does |
|---|---|---|
| **DING** — metadata manager | Extractor | Schema discovery, drift detection, propagation |
| **DONG** — execution engine | Extractor, Loader | Multi-threaded bulk read/write, connector management |
| Source connectors | Extractor | SQL Server, Oracle, SQLite, CSV, MS Access |
| Target connectors | Loader | Same set + data warehouse targets |
| Custom Python functions | Transformer | Calculated columns, business logic |
| Version tracking | Executor | Run lineage, schema change history |

Agents call dingDONG operations via AgentDesk's tool interface — the same ReAct loop used for code pipelines, now pointed at data sources.

---

## Slide 4 · Why AgentDesk Data?

### Compared to traditional ETL tools

| Traditional ETL | AgentDesk Data |
|---|---|
| Static pipelines — breaks on schema change | Extractor detects drift, Transformer adapts |
| No explanation of transformations | Every decision logged, searchable in memory |
| Manual retry on failure | Executor retries with context from error logs |
| Separate tools for batch and streaming | Same agent pipeline, different trigger |
| Configuration-heavy | Describe the pipeline in natural language |

### Key design principles

**Agents own their domain**
Each role has exactly the tools it needs. The Extractor cannot write. The Loader cannot modify source schemas. Clean separation prevents side effects.

**Memory makes pipelines smarter over time**
Every run is stored in AgentDesk memory. On the next run, the Transformer can look up how it handled a similar quality issue last month. The Executor can detect that a pipeline has been consistently slow on Mondays.

**Human approval for critical loads**
Set `approval_gate: true` on the Loader stage for production targets. The Transformer produces a preview plan — row counts, target tables, data quality summary — and a human approves before data is written.

**Scheduler + event triggers in one system**
No separate orchestration tool. The Executor agent manages cron schedules for batch pipelines and Kafka subscriptions for event-driven pipelines from a single configuration.

---

### Getting started — pipeline definition (YAML)

```yaml
name: crm_to_dw_daily
description: Extract CRM orders, transform, load to data warehouse
schedule: "0 6 * * *"   # 06:00 UTC daily

stages:
  - key: extractor
    role: Extractor
    approval_gate: false

  - key: transformer
    role: Transformer
    approval_gate: false

  - key: loader
    role: Loader
    approval_gate: true   # human reviews load plan before writing to production DW
    rejection_loops_back_to: transformer

  - key: executor
    role: Executor
    approval_gate: false
```

---

### Streaming pipeline — Kafka trigger

```yaml
name: order_events_streaming
description: Consume order events from Kafka, transform, load incrementally
trigger:
  type: kafka
  topic: orders.created
  consumer_group: agentdesk_etl
  batch_size: 500
  flush_interval_s: 30

stages:
  - key: extractor
    role: Extractor
    config:
      mode: kafka
      topic: orders.created

  - key: transformer
    role: Transformer

  - key: loader
    role: Loader
    config:
      strategy: append
      target: dw.fact_orders_stream
```

---

*AgentDesk Data ETL Solution · Built on dingDONG · v2.0 · 2026*
*dingDONG: https://github.com/biskilled/dingDONG*
