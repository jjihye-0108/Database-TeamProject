-- 판매 실적 상위 5개 매장
SELECT
    st.store_id,
    st.store_name,
    SUM(s.total_amount) AS total_sales
FROM STORE st
JOIN SALES s ON st.store_id = s.store_id
GROUP BY st.store_id, st.store_name
ORDER BY total_sales DESC
LIMIT 5;


-- 각 매장별 판매량 TOP 20 제품
WITH ProductSales AS (
    SELECT
        s.store_id,
        p.product_id,
        p.product_name,
        SUM(sd.quantity) AS total_sold,

        ROW_NUMBER() OVER (
            PARTITION BY s.store_id
            ORDER BY SUM(sd.quantity) DESC
        ) AS rn

    FROM SALES s
    JOIN SALESDETAIL sd
        ON s.sale_id = sd.sale_id
    JOIN PRODUCT p
        ON sd.product_id = p.product_id

    GROUP BY
        s.store_id,
        p.product_id,
        p.product_name
)

SELECT *
FROM ProductSales
WHERE rn <= 20;


-- 시도별 판매량 TOP 20 제품
-- CASE WHEN 중복을 줄이기 위해 StoreRegion CTE로 먼저 지역 분류
WITH StoreRegion AS (
    SELECT
        store_id,
        CASE
            WHEN address LIKE '서울%' THEN '서울'
            WHEN address LIKE '경기%' THEN '경기'
            WHEN address LIKE '인천%' THEN '인천'
            WHEN address LIKE '부산%' THEN '부산'
            WHEN address LIKE '대구%' THEN '대구'
            WHEN address LIKE '대전%' THEN '대전'
            WHEN address LIKE '광주%' THEN '광주'
            WHEN address LIKE '울산%' THEN '울산'
            ELSE '기타'
        END AS region
    FROM STORE
),

RegionSales AS (
    SELECT
        sr.region,
        p.product_id,
        p.product_name,
        SUM(sd.quantity) AS total_sold,

        ROW_NUMBER() OVER (
            PARTITION BY sr.region
            ORDER BY SUM(sd.quantity) DESC
        ) AS rn

    FROM StoreRegion sr
    JOIN SALES s
        ON sr.store_id = s.store_id
    JOIN SALESDETAIL sd
        ON s.sale_id = sd.sale_id
    JOIN PRODUCT p
        ON sd.product_id = p.product_id

    GROUP BY
        sr.region,
        p.product_id,
        p.product_name
)

SELECT
    region,
    product_id,
    product_name,
    total_sold
FROM RegionSales
WHERE rn <= 20;


-- 펩시가 코카콜라보다 많이 팔린 매장 수
WITH BrandSales AS (
    SELECT
        s.store_id,
        b.brand_name,
        SUM(sd.quantity) AS qty

    FROM SALES s
    JOIN SALESDETAIL sd
        ON s.sale_id = sd.sale_id
    JOIN PRODUCT p
        ON sd.product_id = p.product_id
    JOIN BRAND b
        ON p.brand_id = b.brand_id

    WHERE b.brand_name IN ('Pepsi', 'Coca-Cola')

    GROUP BY
        s.store_id,
        b.brand_name
)

SELECT COUNT(*) AS pepsi_wins
FROM (
    SELECT p.store_id
    FROM BrandSales p
    JOIN BrandSales c
        ON p.store_id = c.store_id
    WHERE
        p.brand_name = 'Pepsi'
        AND c.brand_name = 'Coca-Cola'
        AND p.qty > c.qty
) AS t;


-- 우유와 함께 구매한 상품 TOP 3
SELECT
    p2.product_name,
    COUNT(*) AS frequency

FROM SALESDETAIL milk
JOIN PRODUCT pm
    ON milk.product_id = pm.product_id

JOIN SALESDETAIL other
    ON milk.sale_id = other.sale_id

JOIN PRODUCT p2
    ON other.product_id = p2.product_id

WHERE
    (
        pm.product_name LIKE '%Milk%'
        OR pm.product_name LIKE '%우유%'
    )
    AND milk.product_id <> other.product_id

GROUP BY
    p2.product_id,
    p2.product_name

ORDER BY frequency DESC
LIMIT 3;


-- 재고 부족 상품
SELECT
    i.store_id,
    p.product_name,
    i.quantity,
    i.safety_stock
FROM INVENTORY i
JOIN PRODUCT p
    ON i.product_id = p.product_id
WHERE i.quantity <= i.safety_stock;


-- 브랜드별 매출 순위
SELECT
    b.brand_name,
    SUM(sd.quantity * sd.unit_price) AS revenue

FROM SALESDETAIL sd
JOIN PRODUCT p
    ON sd.product_id = p.product_id
JOIN BRAND b
    ON p.brand_id = b.brand_id

GROUP BY
    b.brand_id,
    b.brand_name

ORDER BY revenue DESC;