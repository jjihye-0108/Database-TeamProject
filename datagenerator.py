from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date, timedelta

DB_DEFAULT = "convenience.db"
random.seed(42)

# ============================================================
# 카테고리: parent_category_id로 계층 구조 표현
# (category_name, parent_name or None)
# ============================================================
CATEGORY_TREE = [
    ("식품",        None),
    ("음료",        "식품"),
    ("탄산음료",    "음료"),
    ("유제품",      "식품"),
    ("스낵",        "식품"),
    ("라면",        "식품"),
    ("간편식",      "식품"),
    ("아이스크림",  "식품"),
    ("생활용품",    None),
]

BRANDS = [
    "Pepsi", "Coca-Cola", "Seoul Dairy", "Maeil", "Lotte",
    "Nongshim", "Orion", "Haitai", "Samyang", "CJ",
    "Pulmuone", "Dongwon",
]

# (barcode, product_name, brand_name, category_name, base_price, unit)
# category_name은 PRODUCTCATEGORYMAP에 매핑하기 위해서만 사용 (PRODUCT 테이블에는 컬럼 없음)
PRODUCT_SEEDS = [
    ("880000000001", "Pepsi Zero 500ml",        "Pepsi",       "탄산음료",   1900, "개"),
    ("880000000002", "Pepsi Cola 1.5L",          "Pepsi",       "탄산음료",   3200, "개"),
    ("880000000003", "Coca-Cola Zero 500ml",     "Coca-Cola",   "탄산음료",   2000, "개"),
    ("880000000004", "Coca-Cola Original 1.5L",  "Coca-Cola",   "탄산음료",   3400, "개"),
    ("880000000005", "Seoul Milk 1L",            "Seoul Dairy", "유제품",     3200, "개"),
    ("880000000006", "Maeil Milk 1L",            "Maeil",       "유제품",     3300, "개"),
    ("880000000007", "Banana Milk",              "Maeil",       "유제품",     1800, "개"),
    ("880000000008", "Shrimp Crackers",          "Nongshim",    "스낵",       1700, "개"),
    ("880000000009", "Choco Pie",                "Orion",       "스낵",       4800, "개"),
    ("880000000010", "Potato Chips",             "Lotte",       "스낵",       1800, "개"),
    ("880000000011", "Shin Ramen",               "Nongshim",    "라면",       1200, "개"),
    ("880000000012", "Buldak Ramen",             "Samyang",     "라면",       1500, "개"),
    ("880000000013", "Triangle Kimbap Tuna",     "CJ",          "간편식",     1400, "개"),
    ("880000000014", "Lunch Box Bulgogi",        "CJ",          "간편식",     5200, "개"),
    ("880000000015", "Bottled Water 500ml",      "Lotte",       "음료",       900,  "개"),
    ("880000000016", "Americano Can",            "Lotte",       "음료",       1700, "개"),
    ("880000000017", "Wet Tissue",               "Dongwon",     "생활용품",   1500, "개"),
    ("880000000018", "Cup Ice",                  "Haitai",      "아이스크림", 800,  "개"),
]

# [추가] queries.sql ⑩번(여러 카테고리에 속하는 제품) 쿼리가 의미 있는 결과를 내도록
# 위 제품 중 일부를 추가 카테고리에도 매핑한다. (product_name, extra_category_name)
EXTRA_CATEGORY_MAP = [
    ("Wet Tissue", "식품"),  # 생활용품 + 식품(편의상 비치) 등 다중 카테고리 예시
    ("Cup Ice", "음료"),     # 아이스크림 + 음료
]

STORE_DATA = [
    ("Emart24 Ewha Asan Engineering", "서울특별시 서대문구 이화여대길 52 이화여자대학교 아산공학관", "02-1234-0001", "08:00-22:00"),
    ("Emart24 Ewha Main Gate",        "서울특별시 서대문구 이화여대길 50",                          "02-1234-0002", "00:00-24:00"),
    ("Emart24 Sinchon Station",       "서울특별시 서대문구 신촌로 83",                              "02-1234-0003", "00:00-24:00"),
    ("Emart24 Yonsei Engineering",    "서울특별시 서대문구 연세로 50",                              "02-1234-0004", "08:00-23:00"),
    ("Emart24 Hongdae",               "서울특별시 마포구 양화로 45",                                "02-1234-0005", "00:00-24:00"),
    ("Emart24 Uijeongbu",             "경기도 의정부시 시민로 77",                                  "031-1234-0006", "00:00-24:00"),
    ("Emart24 Incheon Songdo",        "인천광역시 연수구 송도국제대로 10",                          "032-1234-0007", "00:00-24:00"),
    ("Emart24 Busan Haeundae",        "부산광역시 해운대구 해운대로 101",                           "051-1234-0008", "00:00-24:00"),
]

SUPPLIER_DATA = [
    ("Supplier A", "홍길동", "02-2000-0001", "supplier_a@example.com", "서울특별시 중구 공급로 1"),
    ("Supplier B", "김철수", "02-2000-0002", "supplier_b@example.com", "서울특별시 중구 공급로 2"),
    ("Supplier C", "이영희", "02-2000-0003", "supplier_c@example.com", "서울특별시 중구 공급로 3"),
    ("Supplier D", "박민준", "02-2000-0004", "supplier_d@example.com", "서울특별시 중구 공급로 4"),
    ("Supplier E", "최수연", "02-2000-0005", "supplier_e@example.com", "서울특별시 중구 공급로 5"),
]

# [추가] SUPPLIER_BRAND 매핑용: 각 공급업체가 취급하는 브랜드 (supplier_name, [brand_name, ...])
SUPPLIER_BRAND_DATA = [
    ("Supplier A", ["Pepsi", "Coca-Cola"]),
    ("Supplier B", ["Seoul Dairy", "Maeil"]),
    ("Supplier C", ["Lotte", "Orion", "Haitai"]),
    ("Supplier D", ["Nongshim", "Samyang"]),
    ("Supplier E", ["CJ", "Pulmuone", "Dongwon"]),
]


# ============================================================
# 유틸
# ============================================================

def get_columns(cur: sqlite3.Cursor, table: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def insert_row(cur: sqlite3.Cursor, table: str, row: dict) -> int:
    cols = get_columns(cur, table)
    filtered = {k: v for k, v in row.items() if k in cols}
    sql = (
        f"INSERT INTO {table} ({', '.join(filtered.keys())}) "
        f"VALUES ({', '.join(['?'] * len(filtered))})"
    )
    cur.execute(sql, tuple(filtered.values()))
    return cur.lastrowid


def clear_tables(cur: sqlite3.Cursor) -> None:
    """외래키 의존 순서대로 삭제"""
    tables = [
        "DELIVERY", "ORDERDETAIL", "PURCHASEORDER",
        "SALESDETAIL", "SALES",
        "INVENTORY",
        "PRODUCTCATEGORYMAP", "SUPPLIER_BRAND",
        "PRODUCT", "PRODUCTCATEGORY", "BRAND",
        "MEMBER", "GUEST", "CUSTOMER",
        "STORE", "SUPPLIER",
    ]
    for t in tables:
        cur.execute(f"DELETE FROM {t}")


# ============================================================
# 데이터 생성 함수
# ============================================================

def generate_categories(cur: sqlite3.Cursor) -> dict[str, int]:
    """계층 구조 카테고리 INSERT → {category_name: category_id}"""
    name_to_id: dict[str, int] = {}
    for name, parent_name in CATEGORY_TREE:
        parent_id = name_to_id[parent_name] if parent_name else None
        cid = insert_row(cur, "PRODUCTCATEGORY", {
            "category_name": name,
            "parent_category_id": parent_id,
        })
        name_to_id[name] = cid
    return name_to_id


def generate_brands(cur: sqlite3.Cursor) -> dict[str, int]:
    name_to_id: dict[str, int] = {}
    for brand in BRANDS:
        bid = insert_row(cur, "BRAND", {"brand_name": brand})
        name_to_id[brand] = bid
    return name_to_id


def generate_suppliers(cur: sqlite3.Cursor) -> list[int]:
    ids = []
    for name, contact, phone, email, address in SUPPLIER_DATA:
        sid = insert_row(cur, "SUPPLIER", {
            "supplier_name": name,
            "contact_name": contact,
            "contact_phone": phone,
            "email": email,
            "address": address,
        })
        ids.append(sid)
    return ids


def generate_supplier_brands(
    cur: sqlite3.Cursor,
    supplier_name_to_id: dict[str, int],
    brand_map: dict[str, int],
) -> None:
    """[추가] SUPPLIER_BRAND 매핑 INSERT (queries.sql ⑧번 쿼리용)"""
    for supplier_name, brand_names in SUPPLIER_BRAND_DATA:
        supplier_id = supplier_name_to_id[supplier_name]
        for brand_name in brand_names:
            insert_row(cur, "SUPPLIER_BRAND", {
                "supplier_id": supplier_id,
                "brand_id": brand_map[brand_name],
            })


def generate_products(
    cur: sqlite3.Cursor,
    brand_map: dict[str, int],
    category_map: dict[str, int],
) -> list[tuple[int, int]]:
    """
    INSERT products → [(product_id, base_price), ...]
    PRODUCT 테이블에는 category_id 컬럼이 없으므로(스키마상 N:M 관계),
    카테고리 연결은 PRODUCTCATEGORYMAP에 별도로 INSERT한다.
    """
    result = []
    name_to_id: dict[str, int] = {}

    for barcode, name, brand, category, price, unit in PRODUCT_SEEDS:
        pid = insert_row(cur, "PRODUCT", {
            "product_name": name,
            "barcode": barcode,
            "base_price": price,
            "unit": unit,
            "brand_id": brand_map[brand],
        })
        result.append((pid, price))
        name_to_id[name] = pid

        # 기본 카테고리 매핑
        insert_row(cur, "PRODUCTCATEGORYMAP", {
            "product_id": pid,
            "category_id": category_map[category],
        })

    # [추가] 일부 제품은 추가 카테고리에도 매핑 (다대다 관계 / 쿼리 ⑩번용)
    for product_name, extra_category in EXTRA_CATEGORY_MAP:
        pid = name_to_id[product_name]
        cid = category_map[extra_category]
        cur.execute(
            "SELECT 1 FROM PRODUCTCATEGORYMAP WHERE product_id = ? AND category_id = ?",
            (pid, cid),
        )
        if cur.fetchone() is None:
            insert_row(cur, "PRODUCTCATEGORYMAP", {
                "product_id": pid,
                "category_id": cid,
            })

    return result


def generate_stores(cur: sqlite3.Cursor) -> list[int]:
    ids = []
    for name, address, phone, hours in STORE_DATA:
        sid = insert_row(cur, "STORE", {
            "store_name": name,
            "address": address,
            "phone": phone,
            "opening_hours": hours,
        })
        ids.append(sid)
    return ids


def generate_customers(cur: sqlite3.Cursor, count: int = 150) -> list[int]:
    """
    CUSTOMER INSERT 후 MEMBER / GUEST subclass에도 INSERT.
    - 앞 100명: MEMBER (membership_grade 랜덤)
    - 나머지 50명: GUEST
    일부 고객은 개인정보 제공 미동의 → phone/email NULL
    """
    grades = ["Bronze", "Silver", "Gold", "VIP"]
    customer_ids = []
    for i in range(1, count + 1):
        phone = None if i % 7 == 0 else f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        email = None if i % 5 == 0 else f"customer{i}@example.com"
        cid = insert_row(cur, "CUSTOMER", {
            "customer_name": f"Customer {i}",
            "phone": phone,
            "email": email,
        })
        customer_ids.append(cid)
        if i <= 100:
            insert_row(cur, "MEMBER", {
                "customer_id": cid,
                "membership_grade": random.choice(grades),
            })
        else:
            insert_row(cur, "GUEST", {"customer_id": cid})
    return customer_ids


def generate_inventory(
    cur: sqlite3.Cursor,
    store_ids: list[int],
    products: list[tuple[int, int]],
) -> None:
    for store_id in store_ids:
        for product_id, base_price in products:
            # 자동 발주 테스트를 위해 일부 재고는 낮게 생성
            if random.random() < 0.2:
                qty = random.randint(0, 10)
            else:
                qty = random.randint(100, 300)
            safety = random.randint(5, 20)
            insert_row(cur, "INVENTORY", {
                "store_id": store_id,
                "product_id": product_id,
                "quantity": qty,
                "safety_stock": safety,
                "last_updated": date.today().isoformat(),
                "store_price": round(base_price * random.uniform(1.1, 1.3)),
            })


def generate_sales(
    cur: sqlite3.Cursor,
    store_ids: list[int],
    customer_ids: list[int],
    products: list[tuple[int, int]],
    sale_count: int = 600,
) -> None:
    today = date.today()
    main_store_id = store_ids[0]
    # 우유 product_id 직접 추출 (인덱스 4,5,6 = Seoul Milk, Maeil Milk, Banana Milk)
    milk_product_ids = {products[4][0], products[5][0], products[6][0]}

    payment_methods = ["cash", "card", "mobile_pay"]

    for _ in range(sale_count):
        store_id = random.choices(
            store_ids,
            weights=[4 if sid == main_store_id else 1 for sid in store_ids],
            k=1,
        )[0]
        customer_id = random.choice(customer_ids)  # CUSTOMER에 등록된 id만 사용
        sale_dt = (today - timedelta(days=random.randint(0, 90))).isoformat() + " 12:00:00"

        sale_id = insert_row(cur, "SALES", {
            "sale_datetime": sale_dt,
            "total_amount": 0,
            "payment_method": random.choice(payment_methods),
            "store_id": store_id,
            "customer_id": customer_id,
        })

        # 우유와 함께 구매 TOP3 쿼리가 의미 있도록 30% 확률로 우유 포함 구성
        if milk_product_ids and random.random() < 0.30:
            milk_pid = random.choice(list(milk_product_ids))
            other_pid = random.choice([pid for pid, _ in products if pid not in milk_product_ids])
            chosen_ids = {milk_pid, other_pid}
            # 추가로 1~2개 더 고르기
            extras = random.sample(
                [pid for pid, _ in products if pid not in chosen_ids],
                k=min(random.randint(0, 2), len(products) - 2),
            )
            chosen_ids.update(extras)
            chosen = [(pid, price) for pid, price in products if pid in chosen_ids]
        else:
            chosen = random.sample(products, k=random.randint(1, min(5, len(products))))

        total = 0
        for product_id, unit_price in chosen:
            qty = random.randint(1, 4)
            total += qty * unit_price
            insert_row(cur, "SALESDETAIL", {
                "sale_id": sale_id,
                "product_id": product_id,
                "quantity": qty,
                "unit_price": unit_price,
                "discount_amount": 0,
            })
            # 재고 차감
            cur.execute(
                "UPDATE INVENTORY SET quantity = MAX(quantity - ?, 0), last_updated = ? "
                "WHERE store_id = ? AND product_id = ?",
                (qty, date.today().isoformat(), store_id, product_id),
            )

        cur.execute("UPDATE SALES SET total_amount = ? WHERE sale_id = ?", (total, sale_id))


def generate_purchase_orders(
    cur: sqlite3.Cursor,
    store_ids: list[int],
    supplier_ids: list[int],
    products: list[tuple[int, int]],
    order_count: int = 100,
    include_partial_status: bool = False,
) -> None:
    """
    PURCHASEORDER + ORDERDETAIL(+ 입고완료/부분입고 시 DELIVERY) 생성.

    include_partial_status=True이면 '부분입고' 상태도 더미데이터에 포함한다.
    '부분입고'인 경우 DELIVERY는 order_quantity보다 적게 생성하여
    transaction.py의 delivery_menu()가 다루는 시나리오(잔여 입고)를 재현한다.
    """
    today = date.today()
    main_store_id = store_ids[0]

    statuses = ["발주완료", "입고완료", "입고완료", "취소"]
    if include_partial_status:
        statuses.append("부분입고")

    for _ in range(order_count):
        order_date = today - timedelta(days=random.randint(0, 60))
        expected_date = order_date + timedelta(days=random.randint(1, 7))
        status = random.choice(statuses)
        store_id = random.choices(
            store_ids,
            weights=[3 if sid == main_store_id else 1 for sid in store_ids],
            k=1,
        )[0]

        order_id = insert_row(cur, "PURCHASEORDER", {
            "order_date": order_date.isoformat(),
            "status": status,
            "expected_arrival_date": expected_date.isoformat(),
            "store_id": store_id,
            "supplier_id": random.choice(supplier_ids),
        })

        chosen_products = random.sample(products, k=random.randint(1, min(4, len(products))))
        for product_id, base_price in chosen_products:
            supply_price = round(base_price * 0.7)  # 공급가 = 판매가의 70%
            order_qty = random.randint(10, 80)
            insert_row(cur, "ORDERDETAIL", {
                "order_id": order_id,
                "product_id": product_id,
                "order_quantity": order_qty,
                "supply_price": supply_price,
            })

            # 입고완료: 전량 입고 / 부분입고: 일부만 입고된 DELIVERY 생성
            if status == "입고완료":
                delivered_qty = order_qty
                insert_row(cur, "DELIVERY", {
                    "delivery_datetime": expected_date.isoformat() + " 10:00:00",
                    "delivered_quantity": delivered_qty,
                    "order_id": order_id,
                    "product_id": product_id,
                })
            elif status == "부분입고":
                # 1 이상 order_qty 미만으로 일부만 입고 (남은 수량이 반드시 존재해야 함)
                delivered_qty = random.randint(1, max(1, order_qty - 1))
                insert_row(cur, "DELIVERY", {
                    "delivery_datetime": expected_date.isoformat() + " 10:00:00",
                    "delivered_quantity": delivered_qty,
                    "order_id": order_id,
                    "product_id": product_id,
                })


# ============================================================
# main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--reset", action="store_true", help="기존 더미 데이터를 삭제하고 다시 생성")
    parser.add_argument("--sales", type=int, default=600)
    parser.add_argument("--orders", type=int, default=100)
    parser.add_argument(
        "--with-partial-status",
        action="store_true",
        help="PURCHASEORDER 상태값에 '부분입고'도 포함시켜 생성",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        if args.reset:
            clear_tables(cur)

        category_map = generate_categories(cur)
        brand_map = generate_brands(cur)
        supplier_ids = generate_suppliers(cur)

        supplier_name_to_id = {name: sid for (name, *_), sid in zip(SUPPLIER_DATA, supplier_ids)}
        generate_supplier_brands(cur, supplier_name_to_id, brand_map)

        products = generate_products(cur, brand_map, category_map)
        store_ids = generate_stores(cur)
        customer_ids = generate_customers(cur)

        generate_inventory(cur, store_ids, products)
        generate_sales(cur, store_ids, customer_ids, products, args.sales)
        generate_purchase_orders(
            cur, store_ids, supplier_ids, products, args.orders,
            include_partial_status=args.with_partial_status,
        )

        conn.commit()
        print("✅ 더미 데이터 생성 완료!")
        print(f"   - 매장: {len(store_ids)}개")
        print(f"   - 상품: {len(products)}개")
        print(f"   - 고객: 150명 (MEMBER 100 + GUEST 50)")
        print(f"   - 판매: {args.sales}건")
        print(f"   - 발주: {args.orders}건 (입고완료/부분입고 건은 DELIVERY도 생성)")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()