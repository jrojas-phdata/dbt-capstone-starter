WITH products AS (

    SELECT * FROM {{ ref('stg_classic_models__products') }}

),

final AS (

    SELECT
        {{ dbt_utils.generate_surrogate_key(['product_code']) }} AS product_pk
        , quantity_in_stock
        , buy_price
        , msrp

    FROM products

)

SELECT * FROM final
