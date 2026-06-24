# SQL Conventions

These conventions are enforced by `.sqlfluff`. Run `sqlfluff lint` before opening a PR.

## Capitalization

| Element | Rule | Example |
|---|---|---|
| Keywords | UPPER | `SELECT`, `FROM`, `WHERE`, `LEFT JOIN` |
| Functions | UPPER | `COALESCE()`, `IFF()`, `DATEADD()` |
| Data types | UPPER | `VARCHAR`, `NUMBER`, `TIMESTAMP_NTZ` |
| Identifiers | UPPER | `ORDER_ID`, `CUSTOMER_NAME` |
| Literals | lower | `'active'`, `'usd'` |
| Boolean literals | lower | `true`, `false`, `null` |

## Formatting

- Max line length: **120 characters**
- Indent with **4 spaces** (no tabs)
- Commas go at the **start** of the line (leading commas)
- One column per line in `SELECT`

```sql
-- Good
SELECT
    order_id
    , customer_id
    , order_date
    , total_amount

FROM {{ ref('stg_orders') }}

-- Bad
SELECT order_id, customer_id, order_date, total_amount FROM {{ ref('stg_orders') }}
```

## Aliasing

- All tables and subqueries **must** have explicit aliases (minimum 3 characters)
- All columns in joins or multi-table queries **must** have explicit aliases
- Use `AS` keyword explicitly

```sql
-- Good
SELECT
    ord.order_id                        AS order_id
    , cus.customer_name                 AS customer_name

FROM {{ ref('stg_orders') }}            AS ord
LEFT JOIN {{ ref('stg_customers') }}    AS cus
    ON ord.customer_id = cus.customer_id

-- Bad
SELECT o.order_id, c.customer_name
FROM stg_orders o
LEFT JOIN stg_customers c ON o.customer_id = c.customer_id
```

## CTEs

- Prefer CTEs over subqueries
- Each CTE should do one thing
- Name CTEs after what they contain, not what they do (`orders` not `get_orders`)
- Final CTE named `final`; last statement is `SELECT * FROM final`

```sql
WITH source AS (

    SELECT * FROM {{ source('raw', 'orders') }}

),

renamed AS (

    SELECT
        id                  AS order_id
        , customer_id
        , created_at        AS order_date
        , status

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
```

## Joins

- Use `LEFT JOIN` by default; use `INNER JOIN` only when you intentionally want to filter rows
- Always put join conditions on their own indented lines
- Never use implicit joins (comma-style)

```sql
-- Good
LEFT JOIN {{ ref('stg_customers') }} AS cus
    ON ord.customer_id = cus.customer_id
    AND ord.is_deleted = false

-- Bad
FROM orders, customers WHERE orders.customer_id = customers.customer_id
```

## Boolean conditions

- Put `AND` / `OR` at the start of the line
- Use `IFF()` for simple ternary logic, `CASE WHEN` for multi-branch

```sql
WHERE
    status = 'active'
    AND deleted_at IS NULL
    AND amount > 0
```

## Snowflake-specific

- Use `TIMESTAMP_NTZ` for timestamps without timezone
- Use `VARCHAR` (not `STRING`) for text columns
- Use `NUMBER(38, 0)` for integers when precision matters
- Prefer `QUALIFY` over a wrapping subquery for window function filters
