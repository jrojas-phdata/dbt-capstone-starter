WITH payments AS (

    SELECT * FROM {{ ref('stg_classic_models__payments') }}

),

final AS (

    SELECT
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_pk
        , check_number
        , payment_date
        , amount

    FROM payments

)

SELECT * FROM final
