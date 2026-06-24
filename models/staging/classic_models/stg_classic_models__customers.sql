WITH source AS (

    SELECT * FROM {{ source('classic_models', 'customers') }}

),

renamed AS (

    SELECT
        customer_number AS customer_id
        , customer_name
        , customer_last_name AS last_name
        , customer_first_name AS first_name
        , phone
        , address_line1 AS address_line_1
        , address_line2 AS address_line_2
        , city
        , state
        , postal_code
        , country
        , sales_rep_employee_number AS sales_rep_employee_id
        , credit_limit::NUMBER(18, 2) AS credit_limit
        , _sync_date AS synced_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
