WITH date_spine AS (

    SELECT * FROM {{ ref('stg_classic_models__date_spine') }}

),

final AS (

    SELECT
        date_day
        , YEAR(date_day) AS date_year
        , QUARTER(date_day) AS date_quarter
        , MONTH(date_day) AS date_month
        , WEEKOFYEAR(date_day) AS date_week
        , DAY(date_day) AS date_day_of_month

    FROM date_spine

)

SELECT * FROM final
