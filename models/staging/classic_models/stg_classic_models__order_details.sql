WITH source AS (

    SELECT * FROM {{ source('classic_models', 'order_details') }}

),

renamed AS (

    SELECT
        order_number AS order_id
        , product_code
        , order_line_number
        , quantity_ordered
        , price_each::NUMBER(18, 2) AS price_each
        , _sync_date AS synced_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
