CREATE TABLE STORE (
    store_id INTEGER PRIMARY KEY,
    store_name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT,
    opening_hours TEXT
);

CREATE TABLE CUSTOMER (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    phone TEXT,
    email TEXT
);

CREATE TABLE MEMBER (
    customer_id INTEGER PRIMARY KEY,
    membership_grade TEXT NOT NULL,

    FOREIGN KEY (customer_id)
        REFERENCES CUSTOMER(customer_id)
);

CREATE TABLE GUEST (
    customer_id INTEGER PRIMARY KEY,

    FOREIGN KEY (customer_id)
        REFERENCES CUSTOMER(customer_id)
);

CREATE TABLE BRAND (
    brand_id INTEGER PRIMARY KEY,
    brand_name TEXT NOT NULL UNIQUE
);

CREATE TABLE PRODUCTCATEGORY (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL,
    description TEXT,
    parent_category_id INTEGER,

    FOREIGN KEY (parent_category_id)
        REFERENCES PRODUCTCATEGORY(category_id),

    CHECK (
        parent_category_id IS NULL
        OR parent_category_id <> category_id
    )
);

CREATE TABLE PRODUCT (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    barcode TEXT UNIQUE,
    base_price REAL CHECK(base_price >= 0),
    size TEXT,
    unit TEXT NOT NULL,
    brand_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,

    FOREIGN KEY (brand_id)
        REFERENCES BRAND(brand_id),

    FOREIGN KEY (category_id)
        REFERENCES PRODUCTCATEGORY(category_id)
);

CREATE TABLE SUPPLIER (
    supplier_id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    contact_phone TEXT NOT NULL,
    email TEXT,
    address TEXT
);

CREATE TABLE SALES (
    sale_id INTEGER PRIMARY KEY,

    sale_datetime TEXT NOT NULL,

    total_amount REAL
        CHECK(total_amount >= 0),

    payment_method TEXT NOT NULL
        CHECK (
            payment_method IN
            ('cash', 'card', 'mobile_pay')
        ),

    store_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,

    FOREIGN KEY (store_id)
        REFERENCES STORE(store_id),

    FOREIGN KEY (customer_id)
        REFERENCES CUSTOMER(customer_id)
);

CREATE TABLE PURCHASEORDER (
    order_id INTEGER PRIMARY KEY,

    order_date TEXT NOT NULL,

    status TEXT NOT NULL,

    expected_arrival_date TEXT,

    store_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,

    FOREIGN KEY (store_id)
        REFERENCES STORE(store_id),

    FOREIGN KEY (supplier_id)
        REFERENCES SUPPLIER(supplier_id),

    -- relational schema 문서 명시 제약: 도착 예정일은 발주일 이후여야 함
    CHECK (
        expected_arrival_date IS NULL
        OR expected_arrival_date >= order_date
    )
);

CREATE TABLE INVENTORY (
    store_id INTEGER,
    product_id INTEGER,

    quantity INTEGER
        CHECK(quantity >= 0),

    safety_stock INTEGER
        CHECK(safety_stock >= 0),

    last_updated TEXT NOT NULL,

    store_price REAL
        CHECK(store_price >= 0),

    PRIMARY KEY (store_id, product_id),

    FOREIGN KEY (store_id)
        REFERENCES STORE(store_id),

    FOREIGN KEY (product_id)
        REFERENCES PRODUCT(product_id)
);

CREATE TABLE SALESDETAIL (
    sale_id INTEGER,
    product_id INTEGER,

    quantity INTEGER
        CHECK(quantity > 0),

    unit_price REAL
        CHECK(unit_price >= 0),

    discount_amount REAL
        DEFAULT 0
        CHECK(discount_amount >= 0),

    PRIMARY KEY (sale_id, product_id),

    FOREIGN KEY (sale_id)
        REFERENCES SALES(sale_id),

    FOREIGN KEY (product_id)
        REFERENCES PRODUCT(product_id)
);

CREATE TABLE ORDERDETAIL (
    order_id INTEGER,
    product_id INTEGER,

    order_quantity INTEGER
        CHECK(order_quantity > 0),

    supply_price REAL
        CHECK(supply_price >= 0),

    PRIMARY KEY (order_id, product_id),

    FOREIGN KEY (order_id)
        REFERENCES PURCHASEORDER(order_id),

    FOREIGN KEY (product_id)
        REFERENCES PRODUCT(product_id)
);

CREATE TABLE DELIVERY (
    delivery_id INTEGER PRIMARY KEY,

    delivery_datetime TEXT NOT NULL,

    delivered_quantity INTEGER
        CHECK(delivered_quantity > 0),

    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,

    FOREIGN KEY (order_id, product_id)
        REFERENCES ORDERDETAIL(order_id, product_id)
);

-- 인덱스
CREATE INDEX idx_sales_store
ON SALES(store_id);

CREATE INDEX idx_sales_customer
ON SALES(customer_id);

CREATE INDEX idx_sales_datetime
ON SALES(sale_datetime);

CREATE INDEX idx_product_brand
ON PRODUCT(brand_id);

CREATE INDEX idx_product_category
ON PRODUCT(category_id);

CREATE INDEX idx_inventory_store_product
ON INVENTORY(store_id, product_id);

CREATE INDEX idx_purchaseorder_supplier
ON PURCHASEORDER(supplier_id);

CREATE INDEX idx_purchaseorder_store
ON PURCHASEORDER(store_id);
