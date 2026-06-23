# dbt Conventions

## Layer architecture

```
sources → staging → intermediate → marts
```

| Layer | Prefix | Schema | Materialization | Purpose |
|---|---|---|---|---|
| Staging | `stg_` | `stage` | view | 1-to-1 with source, rename & cast only |
| Intermediate | `int_` | `intermediate` | table | Business logic, joins across staging |
| Marts | `dim_` / `fct_` | `data_mart` | table | Consumption-ready, wide, business-named |

## Naming

- **Files and models**: `snake_case`, always prefixed by layer (`stg_`, `int_`, `dim_`, `fct_`)
- **Primary keys**: `<entity>_id` — e.g., `order_id`, `customer_id`
- **Surrogate keys**: generated with `dbt_utils.generate_surrogate_key()`
- **Booleans**: prefix with `is_` or `has_` — e.g., `is_deleted`, `has_refund`
- **Dates**: suffix with `_date` (`order_date`); timestamps with `_at` (`created_at`)

## Staging models

- One staging model per source table
- Rename columns to project-standard names here (never in intermediate/marts)
- Cast all types explicitly; do not rely on implicit casting
- Add `is_deleted` flag if source has soft deletes
- No business logic — no joins, no aggregations, no derived columns beyond renaming/casting

```sql
-- stg_crm__customers.sql
WITH source AS (

    SELECT * FROM {{ source('raw_crm', 'customers') }}

),

renamed AS (

    SELECT
        id                              AS customer_id
        , UPPER(first_name)             AS first_name
        , UPPER(last_name)              AS last_name
        , email                         AS email_address
        , created_at::TIMESTAMP_NTZ     AS created_at
        , is_deleted::BOOLEAN           AS is_deleted

    FROM source

)

SELECT * FROM renamed
```

## Intermediate models

- Combine and reshape staging models
- Express one unit of business logic per model
- Always filter out deleted/invalid records here (not in marts)
- Acceptable to use window functions, aggregations, and complex joins

## Mart models

- Dimension tables (`dim_`): descriptive attributes of an entity, one row per entity
- Fact tables (`fct_`): immutable event records, one row per event
- Always include a surrogate key as the first column
- Include `created_at` and `updated_at` metadata columns where applicable

## Materialization strategy

| Pattern | Materialization | Reason |
|---|---|---|
| Staging | view | Low cost, always fresh |
| Intermediate | table | Avoid re-computing joins on every downstream query |
| Marts | table | Predictable query performance for BI tools |
| Large incrementals | incremental | Cost control on large event tables |

## Incremental models

- Always define `unique_key`
- Use `merge` strategy on Snowflake (default)
- Wrap the incremental filter in `{% if is_incremental() %}`

```sql
{{
    config(
        materialized='incremental',
        unique_key='event_id',
        on_schema_change='append_new_columns'
    )
}}

SELECT ...
FROM {{ ref('stg_events') }}

{% if is_incremental() %}
WHERE event_at > (SELECT MAX(event_at) FROM {{ this }})
{% endif %}
```

## Testing requirements

Every model must have:
- `not_null` + `unique` on the primary key
- `accepted_values` on any status/type column
- At least one `relationships` test where foreign keys exist

Coverage targets (enforced by `dbt_project_evaluator`):
- **Documentation coverage**: ≥ 75%
- **Test coverage**: ≥ 75%

## `ref()` and `source()`

- Always use `{{ ref('model_name') }}` to reference project models
- Always use `{{ source('source_name', 'table_name') }}` for raw sources
- Never hard-code database/schema names in SQL

## Packages

| Package | Purpose |
|---|---|
| `dbt_project_evaluator` | Enforces coverage and structure rules |
| `dbt_utils` | Utility macros (surrogate keys, date spines, etc.) |

Add new packages to `packages.yml` and run `dbt deps` before use.

## Running dbt

```bash
# Install packages
dbt deps

# Full build
dbt build

# Build specific layer
dbt build --select staging
dbt build --select marts

# Build a model and all downstream
dbt build --select +dim_customer+

# Test only
dbt test --select dim_customer

# Compile only (no execution)
dbt compile

# Generate and serve docs
dbt docs generate && dbt docs serve
```
