WITH source AS (

    SELECT * FROM {{ source('classic_models', 'products') }}

),

renamed AS (

    SELECT
        product_code
        , product_name
        , product_line
        , product_scale
        , product_vendor
        , product_description
        , quantity_in_stock
        , buy_price::NUMBER(18, 2) AS buy_price
        , msrp::NUMBER(18, 2) AS msrp
        , _sync_date AS synced_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
