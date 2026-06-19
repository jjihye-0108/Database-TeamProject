-- ① 판매 실적 상위 5개 매장
SELECT
    st.store_id,
    st.store_name,
    SUM(s.total_amount) AS total_sales
FROM STORE st
JOIN SALES s ON st.store_id = s.store_id
GROUP BY st.store_id, st.store_name
ORDER BY total_sales DESC
LIMIT 5;


-- ② 각 매장별 판매량 TOP 20 제품
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
    JOIN SALESDETAIL sd  ON s.sale_id     = sd.sale_id
    JOIN PRODUCT p       ON sd.product_id = p.product_id
    GROUP BY s.store_id, p.product_id, p.product_name
)
SELECT store_id, product_id, product_name, total_sold
FROM ProductSales
WHERE rn <= 20;


-- ③ 시도별 판매량 TOP 20 제품
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
    JOIN SALES s         ON sr.store_id   = s.store_id
    JOIN SALESDETAIL sd  ON s.sale_id     = sd.sale_id
    JOIN PRODUCT p       ON sd.product_id = p.product_id
    GROUP BY sr.region, p.product_id, p.product_name
)
SELECT region, product_id, product_name, total_sold
FROM RegionSales
WHERE rn <= 20;


-- ④ 펩시가 코카콜라보다 많이 팔린 매장 수
WITH BrandSales AS (
    SELECT
        s.store_id,
        b.brand_name,
        SUM(sd.quantity) AS qty
    FROM SALES s
    JOIN SALESDETAIL sd  ON s.sale_id     = sd.sale_id
    JOIN PRODUCT p       ON sd.product_id = p.product_id
    JOIN BRAND b         ON p.brand_id    = b.brand_id
    WHERE b.brand_name IN ('Pepsi', 'Coca-Cola')
    GROUP BY s.store_id, b.brand_name
)
SELECT COUNT(*) AS pepsi_wins
FROM (
    SELECT p.store_id
    FROM BrandSales p
    JOIN BrandSales c ON p.store_id = c.store_id
    WHERE p.brand_name = 'Pepsi'
      AND c.brand_name = 'Coca-Cola'
      AND p.qty > c.qty
);


-- ⑤ 우유와 함께 구매한 상품 TOP 3
SELECT
    p2.product_name,
    COUNT(*) AS frequency
FROM SALESDETAIL milk
JOIN PRODUCT pm   ON milk.product_id = pm.product_id
JOIN SALESDETAIL other ON milk.sale_id = other.sale_id
JOIN PRODUCT p2   ON other.product_id = p2.product_id
WHERE (pm.product_name LIKE '%Milk%' OR pm.product_name LIKE '%우유%')
  AND milk.product_id <> other.product_id
GROUP BY p2.product_id, p2.product_name
ORDER BY frequency DESC
LIMIT 3;


-- ⑥ 재고 부족 상품 (자동 재주문 대상 탐지에도 활용)
SELECT
    i.store_id,
    p.product_name,
    i.quantity,
    i.safety_stock
FROM INVENTORY i
JOIN PRODUCT p ON i.product_id = p.product_id
WHERE i.quantity <= i.safety_stock;


-- ⑦ 브랜드별 매출 순위
SELECT
    b.brand_name,
    SUM(sd.quantity * sd.unit_price) AS revenue
FROM SALESDETAIL sd
JOIN PRODUCT p ON sd.product_id = p.product_id
JOIN BRAND b   ON p.brand_id    = b.brand_id
GROUP BY b.brand_id, b.brand_name
ORDER BY revenue DESC;


-- ⑧ [추가] 특정 공급업체가 취급하는 브랜드 목록 조회
--    (SUPPLIER_BRAND 테이블 활용 예시)
SELECT
    s.supplier_name,
    b.brand_name
FROM SUPPLIER_BRAND sb
JOIN SUPPLIER s ON sb.supplier_id = s.supplier_id
JOIN BRAND b    ON sb.brand_id    = b.brand_id
ORDER BY s.supplier_name, b.brand_name;


-- ⑨ [추가] 특정 카테고리에 속하는 제품 목록 조회
--    (PRODUCTCATEGORYMAP 테이블 활용 예시)
--    예: '탄산음료' 카테고리에 속한 제품
SELECT
    p.product_id,
    p.product_name,
    pc.category_name
FROM PRODUCT p
JOIN PRODUCTCATEGORYMAP pcm ON p.product_id  = pcm.product_id
JOIN PRODUCTCATEGORY pc     ON pcm.category_id = pc.category_id
WHERE pc.category_name = '탄산음료'
ORDER BY p.product_name;


-- ⑩ [추가] 여러 카테고리에 속하는 제품 확인
--    예: '식품'과 '주방용품' 두 카테고리에 모두 속한 제품 (베이킹소다 등)
SELECT
    p.product_id,
    p.product_name,
    COUNT(DISTINCT pcm.category_id) AS category_count
FROM PRODUCT p
JOIN PRODUCTCATEGORYMAP pcm ON p.product_id = pcm.product_id
GROUP BY p.product_id, p.product_name
HAVING category_count > 1
ORDER BY category_count DESC;