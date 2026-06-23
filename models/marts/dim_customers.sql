WITH customers AS (

    SELECT * FROM {{ ref('stg_classic_models__customers') }}

),

final AS (

    SELECT
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_pk
        , customer_name
        , last_name
        , first_name
        , sales_rep_employee_id
        , credit_limit
        , phone
        , address_line_1
        , address_line_2
        , city
        , state
        , postal_code
        , country

    FROM customers

)

SELECT * FROM final
