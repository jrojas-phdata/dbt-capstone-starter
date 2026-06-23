# dbt Capstone Project — Claude Context

See [README.md](README.md) for project overview, business context, source/target ERDs, and model file structure.

## Git

- Do **not** add `Co-Authored-By: Claude` trailers to commit messages.

## Conventions — read before writing code

- [docs/SQL_CONVENTIONS.md](docs/SQL_CONVENTIONS.md) — SQL style rules enforced by sqlfluff
- [docs/YAML_STYLE.md](docs/YAML_STYLE.md) — how to write schema.yml and sources.yml
- [docs/DBT_CONVENTIONS.md](docs/DBT_CONVENTIONS.md) — model naming, layer rules, testing requirements

**Quick reference:**
- SQL keywords/functions UPPER, column identifiers lowercase, literals lower (sqlfluff CP02 enforces lowercase for column refs)
- Leading commas, one column per line
- CTEs over subqueries; final CTE named `final`; end with `SELECT * FROM final`
- All aliases explicit with `AS` (≥ 3 chars)
- PKs: `<entity>_id`; surrogate keys via `dbt_utils.generate_surrogate_key()`
- Booleans: `is_*` / `has_*` prefix
- Model prefixes: `stg_`, `int_`, `dim_`, `fct_`
- Staging model file names: `stg_<source>__<table>.sql` (double underscore between source and table, e.g. `stg_classic_models__orders.sql`)
- Source YAML file name: `_<source>__sources.yml` (e.g. `_classic_models__sources.yml`) — lives in the staging subfolder for that source
- Staging: rename + cast only — no joins, no business logic
- Every mart model must have a description and PK tests

## Schema naming

`generate_schema_name` macro (`macros/system/generate_schema_name.sql`):
- **dev / default** → `<target_schema>_<custom_schema>` (e.g., `JSROJAS_STAGE`)
- **ci / prod** → `<custom_schema>` directly (e.g., `STAGE`)

Layer → custom schema (from `dbt_project.yml` under `models.dim_model`):

| Layer | Custom schema | Dev example |
|-------|--------------|-------------|
| staging | `stage` | `JSROJAS_STAGE` |
| intermediate | `intermediate` | `JSROJAS_INTERMEDIATE` |
| marts | `data_mart` | `JSROJAS_DATA_MART` |

## Running dbt

```bash
dbt deps                           # always run after cloning
dbt build                          # run + test everything
dbt build --select staging         # staging layer only
dbt build --select +dim_customer+  # model + upstream + downstream
dbt test --select dim_customer     # tests only
dbt docs generate && dbt docs serve
```

## Quality gates (CI-enforced)

`dbt_project_evaluator` requires: ≥ 75% doc coverage, ≥ 75% test coverage, `unique` + `not_null` PK pair, fan-out ≤ 5, mart prefix `dim_` or `fct_`.

CI workflows: `.github/workflows/dbt_slim_ci.yml` (PR) and `.github/workflows/dbt_merge.yml` (merge to main).

## Snowflake MCP server

A local MCP server (`mcp/server.py`) is registered as `snowflake` in `.mcp.json`. Use it proactively whenever you need to inspect live warehouse data.

**Available tools:**

| Tool | Purpose |
|------|---------|
| `list_schemas(database?)` | List schemas in a Snowflake database |
| `list_tables(schema, database?)` | List tables and views in a schema |
| `describe_table(table_name, schema, database?)` | Column names, types, nullability |
| `execute_query(sql)` | Run a read-only SELECT (up to 500 rows) |
| `preview_dbt_model(model_name, limit?)` | Preview rows from a materialized dbt model by name |

**When to use it:**
- Before assuming a source exists, use `list_schemas` / `list_tables` to confirm
- After running a model, use `preview_dbt_model` to verify it materialized correctly
- For data questions, use `execute_query` rather than guessing at values
- To resolve column names or types, use `describe_table` before writing SQL

**Safety rules — never violate:**
- `execute_query` only accepts SELECT and WITH queries; the server blocks DDL/DML automatically
- Do NOT compose or suggest any destructive statement (DROP, DELETE, TRUNCATE, UPDATE, MERGE, CREATE) without the user explicitly requesting it in that message
- If the user asks to modify or delete data, state the exact SQL you would run and ask for explicit confirmation before proceeding
- Never reference CI or prod schemas (`STAGE`, `INTERMEDIATE`, `DATA_MART`) in queries — always use the dev-prefixed schemas (e.g., `JSROJAS_STAGE`) unless explicitly told otherwise

## Known gotchas

**`dbt_project.yml` model key must match the project name.**
The project name is `dim_model` (see `name:` at the top of `dbt_project.yml`). The `models:` block must use the same key:
```yaml
models:
  dim_model:       # ← must match name: 'dim_model'
    staging: ...
```
If the key is wrong (e.g. `data_vault`), the layer configs are silently ignored and all models land in the default schema (`JROJAS`) instead of `JROJAS_STAGE` / `JROJAS_INTERMEDIATE` / `JROJAS_DATA_MART`.

**`accepted_values` test syntax changed in dbt Fusion.**
The `values` list must be nested under `arguments:`:
```yaml
data_tests:
  - accepted_values:
      arguments:
        values: ['active', 'inactive']
```
Using the old format (`values:` at the top level) raises a `DbtYamlValidationError` at parse time.

**`dbt docs generate` is not supported in dbt Fusion — use `dbt compile --write-catalog` instead.**
This also means `target/catalog.json` must be generated before committing, because the `check-model-name-contract` pre-commit hook requires it. Run this once before a commit session:
```bash
dbt compile --write-catalog --quiet
```

**A project-level `profiles.yml` overrides `~/.dbt/profiles.yml`.**
The repo ships a gitignored template `profiles.yml` with placeholder values. If it exists in the project root, dbt reads it first and fails to connect. Delete it (it is gitignored) so dbt falls back to `~/.dbt/profiles.yml`.

## What Claude should do

- Follow SQL and YAML conventions exactly as specified in `docs/`
- Always use `{{ ref() }}` and `{{ source() }}` — never hard-code schema names
- Generate tests for every new model's primary key
- Write descriptions for every new model and its columns
- Use the `generate_schema_name` macro logic when reasoning about where objects land in Snowflake
- Default to views for staging, tables for intermediate and marts, unless told otherwise
- Use the `snowflake` MCP tools to inspect live data rather than making assumptions about schema contents

## Activity completion checklist

After writing any model or config file, always complete these steps before marking an activity done:

1. **Build** — run `dbt build --select <model(s)>` (or the layer, e.g. `--select staging`). Fix any compilation or test errors before continuing.
2. **Verify in Snowflake** — for every model that materializes as a table or view, call `preview_dbt_model(model_name)` via the MCP server to confirm the object exists in Snowflake and rows are populated. For staging views, spot-check at least one model per activity.
3. **Only mark the activity done** once both steps pass without errors.

## Activities

With the base repository forked, and your dbt project set up, it is time to build out the data model that the Solution Architect has provided. Complete the following activities:

- [x] **0. Fix the Snowflake MCP server so `describe_table` works before writing any SQL**
  > **PROBLEM:** `.mcp.json` sets `DBT_PROFILES_DIR` to the project directory, which contains a template `profiles.yml` with placeholder credentials — the MCP server cannot connect.
  > **FIX:** Remove the `DBT_PROFILES_DIR` key from the `env` block in `.mcp.json` so `mcp/server.py` falls back to `~/.dbt/profiles.yml`. Then restart Claude Code to reload the MCP server and verify connectivity with `list_tables(schema=CLASSIC_MODELS)`.

- [x] **1. Create a source file following our naming convention that points to our source tables**
  > **NOTE:** The sources can be found in `SANDBOX.CLASSIC_MODELS`

- [x] **2. Create a staging model for every table in our source following the naming convention above**
  > **REMEMBER:** Staging models should just clean column names and data types.
  > **NOTE:** Make sure to also document your model in the appropriate `.yml` files, and lint every model before committing.
  > **DONE WHEN:** `dbt build --select staging` passes all tests, and `preview_dbt_model` returns rows for every staging model.

- [ ] **3. Build out the various intermediate data sets following our naming conventions**
  > **REMEMBER:** This is where we join data and perform the heavier transformations.
  > **NOTE:** Make sure to also document your model in the appropriate `.yml` files, and lint every model before committing.
  > **DONE WHEN:** `dbt build --select intermediate` passes all tests, and `preview_dbt_model` returns rows for every intermediate model.

- [ ] **4. Build out the various data mart data sets following our naming conventions**
  > **REMEMBER:** This is where we efficiently materialize our data sets.
  > **NOTE:** Make sure to also document your model in the appropriate `.yml` files, and lint every model before committing.
  > **DONE WHEN:** `dbt build --select marts` passes all tests, and `preview_dbt_model` returns rows for every mart model.

- [ ] **5. Bring in the `dbt_utils` package to our project so we can create our date dimension easily**
  > **DONE WHEN:** `dbt deps` succeeds and `dbt build --select staging` still passes.

- [ ] **6. Build a date spine in our stage, and use it to create our date dimension**
  > **NOTE:** Make sure to also document your model in the appropriate `.yml` files.
  > **DONE WHEN:** `dbt build --select stg_classic_models__date_spine dim_date` passes, and `preview_dbt_model('dim_date')` returns rows.

- [ ] **7. Apply appropriate tests to all created models**
  > **NOTE:** All models should have at least PK/FK tests.
  > **DONE WHEN:** `dbt build` passes with zero test failures across all layers.

- [ ] **8. Create an exposure of your final data model**
  > **DONE WHEN:** `dbt build` still passes and `dbt ls --resource-type exposure` lists the exposure.

- [ ] **9. Define at least 5 semantic layer metrics for the data model**
  > **DONE WHEN:** `dbt build` still passes and `dbt ls --resource-type metric` lists at least 5 metrics.

- [ ] **10. Provide a Data Contract on the final Data Model**
  > **NOTE:** Set all other models to private.
  > **DONE WHEN:** `dbt build` still passes with contracts enforced.

- [ ] **11. Run `dbt build` and address any errors raised by the project evaluator**
  > **DONE WHEN:** `dbt build` exits with zero errors, including all `dbt_project_evaluator` tests.

- [ ] **12. Build a dbt job to execute your pipeline**
