WITH orders AS (

    SELECT * FROM {{ ref('stg_classic_models__orders') }}

),

customers AS (

    SELECT * FROM {{ ref('stg_classic_models__customers') }}

),

joined AS (

    SELECT
        ord.order_id
        , ord.order_date
        , ord.required_date
        , ord.shipped_date
        , ord.order_status
        , ord.comments
        , ord.customer_id
        , cst.customer_name
        , cst.last_name
        , cst.first_name
        , cst.phone
        , cst.address_line_1
        , cst.address_line_2
        , cst.city
        , cst.state
        , cst.postal_code
        , cst.country
        , cst.sales_rep_employee_id
        , cst.credit_limit

    FROM orders AS ord
        LEFT JOIN customers AS cst
            ON ord.customer_id = cst.customer_id

),

final AS (

    SELECT * FROM joined

)

SELECT * FROM final
