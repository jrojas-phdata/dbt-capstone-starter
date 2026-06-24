WITH source AS (

    SELECT * FROM {{ source('classic_models', 'offices') }}

),

renamed AS (

    SELECT
        office_code AS office_id
        , city
        , phone
        , address_line1 AS address_line_1
        , address_line2 AS address_line_2
        , state
        , country
        , postal_code
        , territory
        , _sync_date AS synced_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
