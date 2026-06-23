WITH orders AS (

    SELECT * FROM {{ ref('int_orders') }}

),

final AS (

    SELECT
        {{ dbt_utils.generate_surrogate_key(['order_id']) }} AS order_pk
        , required_date
        , shipped_date
        , order_status AS status
        , comments

    FROM orders

)

SELECT * FROM final
