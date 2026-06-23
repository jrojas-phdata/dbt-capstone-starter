WITH source AS (

    SELECT * FROM {{ source('classic_models', 'product_lines') }}

),

renamed AS (

    SELECT
        product_line
        , text_description
        , html_description
        , _sync_date AS synced_at
        -- IMAGE (BINARY) excluded: not used in downstream transformations

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
