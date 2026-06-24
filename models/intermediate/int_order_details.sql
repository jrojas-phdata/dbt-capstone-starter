WITH orders AS (

    SELECT * FROM {{ ref('stg_classic_models__orders') }}

),

order_details AS (

    SELECT * FROM {{ ref('stg_classic_models__order_details') }}

),

products AS (

    SELECT * FROM {{ ref('stg_classic_models__products') }}

),

joined AS (

    SELECT
        dtl.order_id
        , dtl.product_code
        , dtl.order_line_number
        , dtl.quantity_ordered
        , dtl.price_each
        , ord.order_date
        , ord.required_date
        , ord.shipped_date
        , ord.order_status
        , ord.customer_id
        , prd.product_name
        , prd.product_line
        , prd.product_scale
        , prd.product_vendor

    FROM order_details AS dtl
        LEFT JOIN orders AS ord
            ON dtl.order_id = ord.order_id
        LEFT JOIN products AS prd
            ON dtl.product_code = prd.product_code

),

final AS (

    SELECT * FROM joined

)

SELECT * FROM final
