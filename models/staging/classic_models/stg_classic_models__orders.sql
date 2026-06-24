WITH source AS (

    SELECT * FROM {{ source('classic_models', 'orders') }}

),

renamed AS (

    SELECT
        order_number AS order_id
        , order_date
        , required_date
        , shipped_date
        , status AS order_status
        , comments
        , customer_number AS customer_id
        , _sync_date AS synced_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
