WITH order_details AS (

    SELECT * FROM {{ ref('int_order_details') }}

),

final AS (

    SELECT
        {{ dbt_utils.generate_surrogate_key(['order_id']) }} AS order_pk
        , {{ dbt_utils.generate_surrogate_key(['product_code']) }} AS product_pk
        , {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_pk
        , order_line_number
        , product_code
        , quantity_ordered
        , price_each

    FROM order_details

)

SELECT * FROM final
