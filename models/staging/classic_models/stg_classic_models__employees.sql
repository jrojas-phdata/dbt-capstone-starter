WITH source AS (

    SELECT * FROM {{ source('classic_models', 'employees') }}

),

renamed AS (

    SELECT
        employee_number AS employee_id
        , last_name
        , first_name
        , extension AS phone_extension
        , email
        , office_code AS office_id
        , reports_to AS manager_employee_id
        , job_title
        , _sync_date AS synced_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
