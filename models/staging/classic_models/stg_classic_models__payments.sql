WITH source AS (

    SELECT * FROM {{ source('classic_models', 'payments') }}

),

renamed AS (

    SELECT
        customer_number AS customer_id
        , check_number
        , payment_date
        , amount::NUMBER(18, 2) AS amount
        , _sync_date AS synced_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
