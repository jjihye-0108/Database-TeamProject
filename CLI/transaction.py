from __future__ import annotations

import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path


# ============================================================
# DB 연결
# ============================================================

try:
    # 기존 CLI/db.py에 get_connection()이 있으면 그걸 사용
    from db import get_connection
except ImportError:
    # 혹시 import가 안 될 경우를 위한 fallback
    def get_connection():
        db_path = Path(__file__).resolve().parent.parent / "convenience.db"
        return sqlite3.connect(db_path)


# ============================================================
# 공통 유틸 함수
# ============================================================

def open_connection():
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.isolation_level = None
    return conn


def input_int(message: str) -> int:
    while True:
        value = input(message).strip()
        try:
            return int(value)
        except ValueError:
            print("숫자로 입력해주세요.")


def input_positive_int(message: str) -> int:
    while True:
        value = input_int(message)
        if value > 0:
            return value
        print("1 이상의 숫자를 입력해주세요.")


def input_date(message: str) -> str:
    while True:
        value = input(message).strip()
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print("날짜 형식은 YYYY-MM-DD로 입력해주세요. 예: 2026-06-25")


def check_exists(cur: sqlite3.Cursor, table: str, id_col: str, id_value: int) -> bool:
    cur.execute(f"SELECT 1 FROM {table} WHERE {id_col} = ?", (id_value,))
    return cur.fetchone() is not None


def get_inventory(cur: sqlite3.Cursor, store_id: int, product_id: int):
    cur.execute(
        """
        SELECT quantity, store_price
        FROM INVENTORY
        WHERE store_id = ? AND product_id = ?
        """,
        (store_id, product_id),
    )
    return cur.fetchone()


def get_product_base_price(cur: sqlite3.Cursor, product_id: int) -> int:
    cur.execute(
        """
        SELECT base_price
        FROM PRODUCT
        WHERE product_id = ?
        """,
        (product_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise ValueError("존재하지 않는 상품 ID입니다.")
    return int(row[0])


def print_recent_ids(cur: sqlite3.Cursor):
    cur.execute(
        """
        SELECT store_id, store_name
        FROM STORE
        ORDER BY store_id
        LIMIT 8
        """
    )
    stores = cur.fetchall()

    cur.execute(
        """
        SELECT product_id, product_name
        FROM PRODUCT
        ORDER BY product_id
        LIMIT 10
        """
    )
    products = cur.fetchall()

    cur.execute(
        """
        SELECT supplier_id, supplier_name
        FROM SUPPLIER
        ORDER BY supplier_id
        LIMIT 5
        """
    )
    suppliers = cur.fetchall()

    print("\n[참고용 ID 목록]")

    print("\n매장")
    for store_id, store_name in stores:
        print(f"  {store_id}. {store_name}")

    print("\n상품")
    for product_id, product_name in products:
        print(f"  {product_id}. {product_name}")

    print("\n공급업체")
    for supplier_id, supplier_name in suppliers:
        print(f"  {supplier_id}. {supplier_name}")


# ============================================================
# 1. 구매 처리
# SALES INSERT
# SALESDETAIL INSERT
# INVENTORY 재고 차감
# ============================================================

def purchase_menu():
    conn = open_connection()
    cur = conn.cursor()

    try:
        print("\n==============================")
        print(" 구매 처리 ")
        print("==============================")

        print_recent_ids(cur)

        store_id = input_int("\n매장 ID 입력 > ")
        customer_id_input = input("고객 ID 입력, 비회원이면 Enter > ").strip()
        product_id = input_int("상품 ID 입력 > ")
        quantity = input_positive_int("구매 수량 입력 > ")
        payment_method = input("결제수단 입력(cash/card/mobile_pay) > ").strip()

        if payment_method == "":
            payment_method = "card"

        customer_id = None
        if customer_id_input != "":
            customer_id = int(customer_id_input)

        if not check_exists(cur, "STORE", "store_id", store_id):
            print("존재하지 않는 매장 ID입니다.")
            return

        if customer_id is not None and not check_exists(cur, "CUSTOMER", "customer_id", customer_id):
            print("존재하지 않는 고객 ID입니다.")
            return

        if not check_exists(cur, "PRODUCT", "product_id", product_id):
            print("존재하지 않는 상품 ID입니다.")
            return

        inventory = get_inventory(cur, store_id, product_id)
        if inventory is None:
            print("해당 매장에 등록되지 않은 상품입니다.")
            return

        current_quantity, store_price = inventory

        if current_quantity < quantity:
            print(f"재고가 부족합니다. 현재 재고: {current_quantity}")
            return

        unit_price = int(store_price)
        total_amount = unit_price * quantity
        sale_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = date.today().isoformat()

        conn.execute("BEGIN IMMEDIATE")

        cur.execute(
            """
            INSERT INTO SALES (
                sale_datetime,
                total_amount,
                payment_method,
                store_id,
                customer_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                sale_datetime,
                total_amount,
                payment_method,
                store_id,
                customer_id,
            ),
        )

        sale_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO SALESDETAIL (
                sale_id,
                product_id,
                quantity,
                unit_price,
                discount_amount
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                sale_id,
                product_id,
                quantity,
                unit_price,
                0,
            ),
        )

        cur.execute(
            """
            UPDATE INVENTORY
            SET quantity = quantity - ?,
                last_updated = ?
            WHERE store_id = ?
              AND product_id = ?
            """,
            (
                quantity,
                today,
                store_id,
                product_id,
            ),
        )

        conn.commit()

        print("\n구매 처리가 완료되었습니다.")
        print(f"판매 ID: {sale_id}")
        print(f"총 결제 금액: {total_amount}원")
        print(f"차감 후 재고: {current_quantity - quantity}")

    except Exception as e:
        conn.rollback()
        print("\n구매 처리 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


# ============================================================
# 2. 발주 처리
# PURCHASEORDER INSERT
# ORDERDETAIL INSERT
# ============================================================

def order_menu():
    conn = open_connection()
    cur = conn.cursor()

    try:
        print("\n==============================")
        print(" 발주 처리 ")
        print("==============================")

        print_recent_ids(cur)

        store_id = input_int("\n매장 ID 입력 > ")
        supplier_id = input_int("공급업체 ID 입력 > ")
        product_id = input_int("상품 ID 입력 > ")
        order_quantity = input_positive_int("발주 수량 입력 > ")
        expected_arrival_date = input_date("예상 입고일 입력(YYYY-MM-DD) > ")

        order_date = date.today().isoformat()

        if expected_arrival_date < order_date:
            print("예상 입고일은 발주일보다 빠를 수 없습니다.")
            return

        if not check_exists(cur, "STORE", "store_id", store_id):
            print("존재하지 않는 매장 ID입니다.")
            return

        if not check_exists(cur, "SUPPLIER", "supplier_id", supplier_id):
            print("존재하지 않는 공급업체 ID입니다.")
            return

        if not check_exists(cur, "PRODUCT", "product_id", product_id):
            print("존재하지 않는 상품 ID입니다.")
            return

        base_price = get_product_base_price(cur, product_id)
        supply_price = int(base_price * 0.7)

        conn.execute("BEGIN IMMEDIATE")

        cur.execute(
            """
            INSERT INTO PURCHASEORDER (
                order_date,
                status,
                expected_arrival_date,
                store_id,
                supplier_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order_date,
                "발주완료",
                expected_arrival_date,
                store_id,
                supplier_id,
            ),
        )

        order_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO ORDERDETAIL (
                order_id,
                product_id,
                order_quantity,
                supply_price
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                order_id,
                product_id,
                order_quantity,
                supply_price,
            ),
        )

        conn.commit()

        print("\n발주 처리가 완료되었습니다.")
        print(f"발주 ID: {order_id}")
        print(f"상품 ID: {product_id}")
        print(f"발주 수량: {order_quantity}")
        print(f"예상 입고일: {expected_arrival_date}")

    except Exception as e:
        conn.rollback()
        print("\n발주 처리 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


# ============================================================
# 3. 입고 처리
# DELIVERY INSERT
# INVENTORY 재고 증가
# PURCHASEORDER 상태 변경
# ============================================================

def delivery_menu():
    conn = open_connection()
    cur = conn.cursor()

    try:
        print("\n==============================")
        print(" 입고 처리 ")
        print("==============================")

        cur.execute(
            """
            SELECT 
                po.order_id,
                po.store_id,
                s.store_name,
                po.status,
                po.expected_arrival_date
            FROM PURCHASEORDER po
            JOIN STORE s ON po.store_id = s.store_id
            WHERE po.status IN ('발주완료', '부분입고')
            ORDER BY po.order_id
            LIMIT 10
            """
        )
        orders = cur.fetchall()

        print("\n[입고 가능 발주 목록]")
        if not orders:
            print("입고 가능한 발주가 없습니다.")
        else:
            for order_id, store_id, store_name, status, expected_date in orders:
                print(
                    f"  발주ID {order_id} | 매장ID {store_id} | "
                    f"{store_name} | 상태 {status} | 예상입고일 {expected_date}"
                )

        order_id = input_int("\n입고 처리할 발주 ID 입력 > ")
        product_id = input_int("상품 ID 입력 > ")
        delivered_quantity = input_positive_int("입고 수량 입력 > ")

        cur.execute(
            """
            SELECT 
                po.store_id,
                od.order_quantity
            FROM PURCHASEORDER po
            JOIN ORDERDETAIL od ON po.order_id = od.order_id
            WHERE po.order_id = ?
              AND od.product_id = ?
            """,
            (order_id, product_id),
        )
        row = cur.fetchone()

        if row is None:
            print("해당 발주에 포함된 상품이 아닙니다.")
            return

        store_id, order_quantity = row

        cur.execute(
            """
            SELECT COALESCE(SUM(delivered_quantity), 0)
            FROM DELIVERY
            WHERE order_id = ?
              AND product_id = ?
            """,
            (order_id, product_id),
        )
        already_delivered = cur.fetchone()[0]

        remaining_quantity = order_quantity - already_delivered

        if remaining_quantity <= 0:
            print("이미 전량 입고된 상품입니다.")
            return

        if delivered_quantity > remaining_quantity:
            print(f"입고 수량이 남은 발주 수량보다 많습니다. 남은 수량: {remaining_quantity}")
            return

        delivery_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = date.today().isoformat()

        conn.execute("BEGIN IMMEDIATE")

        cur.execute(
            """
            INSERT INTO DELIVERY (
                delivery_datetime,
                delivered_quantity,
                order_id,
                product_id
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                delivery_datetime,
                delivered_quantity,
                order_id,
                product_id,
            ),
        )

        cur.execute(
            """
            UPDATE INVENTORY
            SET quantity = quantity + ?,
                last_updated = ?
            WHERE store_id = ?
              AND product_id = ?
            """,
            (
                delivered_quantity,
                today,
                store_id,
                product_id,
            ),
        )

        if cur.rowcount == 0:
            base_price = get_product_base_price(cur, product_id)
            store_price = int(base_price * 1.2)

            cur.execute(
                """
                INSERT INTO INVENTORY (
                    store_id,
                    product_id,
                    quantity,
                    safety_stock,
                    last_updated,
                    store_price
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    store_id,
                    product_id,
                    delivered_quantity,
                    10,
                    today,
                    store_price,
                ),
            )

        new_total_delivered = already_delivered + delivered_quantity

        if new_total_delivered >= order_quantity:
            new_status = "입고완료"
        else:
            new_status = "부분입고"

        cur.execute(
            """
            UPDATE PURCHASEORDER
            SET status = ?
            WHERE order_id = ?
            """,
            (
                new_status,
                order_id,
            ),
        )

        conn.commit()

        print("\n입고 처리가 완료되었습니다.")
        print(f"발주 ID: {order_id}")
        print(f"상품 ID: {product_id}")
        print(f"이번 입고 수량: {delivered_quantity}")
        print(f"누적 입고 수량: {new_total_delivered}")
        print(f"발주 상태: {new_status}")

    except Exception as e:
        conn.rollback()
        print("\n입고 처리 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


# ============================================================
# 선택 기능: 자동 재주문 발주
# README의 자동 발주 시뮬레이션용
# main.py에 연결하지 않아도 됨
# ============================================================

def auto_reorder_menu():
    conn = open_connection()
    cur = conn.cursor()

    try:
        print("\n==============================")
        print(" 자동 재주문 발주 ")
        print("==============================")

        supplier_id = input_int("자동 발주에 사용할 공급업체 ID 입력 > ")

        if not check_exists(cur, "SUPPLIER", "supplier_id", supplier_id):
            print("존재하지 않는 공급업체 ID입니다.")
            return

        cur.execute(
            """
            SELECT 
                i.store_id,
                i.product_id,
                i.quantity,
                i.safety_stock,
                p.base_price
            FROM INVENTORY i
            JOIN PRODUCT p ON i.product_id = p.product_id
            WHERE i.quantity <= i.safety_stock
            ORDER BY i.store_id, i.product_id
            """
        )

        low_stock_items = cur.fetchall()

        if not low_stock_items:
            print("재고 부족 상품이 없습니다.")
            return

        order_date = date.today().isoformat()
        expected_arrival_date = (date.today() + timedelta(days=3)).isoformat()

        conn.execute("BEGIN IMMEDIATE")

        created_count = 0

        for store_id, product_id, quantity, safety_stock, base_price in low_stock_items:
            reorder_quantity = max((safety_stock * 3) - quantity, 10)
            supply_price = int(base_price * 0.7)

            cur.execute(
                """
                INSERT INTO PURCHASEORDER (
                    order_date,
                    status,
                    expected_arrival_date,
                    store_id,
                    supplier_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    order_date,
                    "발주완료",
                    expected_arrival_date,
                    store_id,
                    supplier_id,
                ),
            )

            order_id = cur.lastrowid

            cur.execute(
                """
                INSERT INTO ORDERDETAIL (
                    order_id,
                    product_id,
                    order_quantity,
                    supply_price
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    product_id,
                    reorder_quantity,
                    supply_price,
                ),
            )

            created_count += 1

        conn.commit()

        print("\n자동 재주문 발주가 완료되었습니다.")
        print(f"생성된 발주 건수: {created_count}")

    except Exception as e:
        conn.rollback()
        print("\n자동 재주문 발주 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


# ============================================================
# transaction.py 단독 실행용 메뉴
# ============================================================

def transaction_menu():
    while True:
        print("\n==============================")
        print(" 구매 / 발주 / 입고 관리 ")
        print("==============================")
        print("1. 구매")
        print("2. 발주")
        print("3. 입고")
        print("4. 자동 재주문 발주")
        print("0. 뒤로가기")

        choice = input("\n메뉴 선택 > ")

        if choice == "1":
            purchase_menu()

        elif choice == "2":
            order_menu()

        elif choice == "3":
            delivery_menu()

        elif choice == "4":
            auto_reorder_menu()

        elif choice == "0":
            break

        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    transaction_menu()
