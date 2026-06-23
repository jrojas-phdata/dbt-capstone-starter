WITH date_spine AS (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2003-01-01' as date)",
        end_date="cast('2006-01-01' as date)"
    ) }}

),

final AS (

    SELECT
        date_day::DATE AS date_day

    FROM date_spine

)

SELECT * FROM final
