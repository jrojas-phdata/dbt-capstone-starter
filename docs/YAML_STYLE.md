# YAML Style Guide

Applies to all dbt YAML files: `schema.yml`, `sources.yml`, `exposures.yml`, `_sources.yml`.

## File naming

- One `schema.yml` per model subdirectory (staging, intermediate, marts)
- Source definitions live in `_sources.yml` inside the relevant `staging/` folder
- Prefix with underscore to sort config files above model files in most editors

## Indentation & whitespace

- 2-space indentation (never tabs)
- One blank line between top-level list items (models, sources, exposures)
- No trailing whitespace

## Model definitions

Order properties consistently:

```yaml
models:
  - name: dim_customer
    description: >
      One row per customer. Combines profile data from the CRM with
      order history from the transactional system.
    config:
      materialized: table
      tags: ['marts', 'daily']
    meta:
      owner: analytics
      domain: customers
    columns:
      - name: customer_id
        description: Surrogate key for the customer.
        data_tests:
          - not_null
          - unique
      - name: customer_name
        description: Full name as provided at registration.
        data_tests:
          - not_null
```

## Column ordering in YAML

1. `name`
2. `description`
3. `data_type` (optional, include for marts)
4. `data_tests`
5. `meta` (optional)

## Tests

- Every model must have `not_null` and `unique` on its primary key
- Use `dbt_utils.expression_is_true` for business-logic assertions
- Use `accepted_values` for low-cardinality status/type columns

```yaml
data_tests:
  - not_null
  - unique
  - accepted_values:
      values: ['active', 'inactive', 'pending']
```

## Descriptions

- Required on every model and every column in `marts/`
- Recommended on staging and intermediate columns
- Use `>` (block scalar) for multi-line descriptions
- Write in third person, present tense: "Returns one row per…"

## Sources

```yaml
sources:
  - name: raw_crm
    database: raw
    schema: crm
    description: Raw CRM data loaded by Fivetran.
    tables:
      - name: customers
        description: One row per CRM customer record.
        columns:
          - name: id
            description: Source system primary key.
            data_tests:
              - not_null
              - unique
```

## Tags

Use tags to group models for selective runs:

- `daily` / `hourly` — refresh cadence
- `pii` — contains personally identifiable information
- `skip_ci` — exclude from slim CI runs (use sparingly)
