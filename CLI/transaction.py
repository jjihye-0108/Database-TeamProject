"""
CLI/transaction.py

구매 / 발주 / 입고 기능 담당 모듈
현재 프로젝트 schema.sql 기준 테이블명을 사용

사용 테이블:
- SALES
- SALESDETAIL
- PURCHASEORDER
- ORDERDETAIL
- DELIVERY
- INVENTORY
- PRODUCT
- CUSTOMER
- STORE
- SUPPLIER

main.py 연결 예시:
    from transaction import transaction_menu

    ...
    elif choice == "4":
        transaction_menu()
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path


# ------------------------------------------------------------
# DB 연결
# ------------------------------------------------------------
# 기존 CLI/db.py에 get_connection()이 있으면 그걸 먼저 사용
# 없거나 실행 위치 때문에 import가 실패하면 프로젝트 루트의 convenience.db에 직접 연결
try:
    from db import get_connection  # type: ignore
except Exception:
    DB_PATH = Path(__file__).resolve().parent.parent / "convenience.db"

    def get_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


# ------------------------------------------------------------
# 공통 유틸
# ------------------------------------------------------------
def input_int(prompt: str, min_value: int | None = None) -> int:
    """정수 입력을 안전하게 받는 함수"""
    while True:
        value = input(prompt).strip()
        try:
            number = int(value)
            if min_value is not None and number < min_value:
                print(f"{min_value} 이상의 숫자를 입력해주세요.")
                continue
            return number
        except ValueError:
            print("숫자로 입력해주세요.")


def input_float(prompt: str, min_value: float | None = None) -> float:
    """실수 입력을 안전하게 받는 함수"""
    while True:
        value = input(prompt).strip()
        try:
            number = float(value)
            if min_value is not None and number < min_value:
                print(f"{min_value} 이상의 숫자를 입력해주세요.")
                continue
            return number
        except ValueError:
            print("숫자로 입력해주세요.")


def today_text() -> str:
    return date.today().isoformat()


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def row_exists(cur: sqlite3.Cursor, table: str, column: str, value: int) -> bool:
    cur.execute(f"SELECT 1 FROM {table} WHERE {column} = ?", (value,))
    return cur.fetchone() is not None


def show_basic_data() -> None:
    """구매/발주/입고 입력 전에 참고할 수 있는 기본 ID 목록 출력"""
    conn = get_connection()
    cur = conn.cursor()

    print("\n[매장 목록]")
    cur.execute("SELECT store_id, store_name FROM STORE ORDER BY store_id LIMIT 10")
    for row in cur.fetchall():
        print(f"{row[0]:>3} | {row[1]}")

    print("\n[상품 목록]")
    cur.execute("SELECT product_id, product_name, base_price FROM PRODUCT ORDER BY product_id LIMIT 20")
    for row in cur.fetchall():
        print(f"{row[0]:>3} | {row[1]} | 기본가 {row[2]}")

    print("\n[공급업체 목록]")
    cur.execute("SELECT supplier_id, supplier_name FROM SUPPLIER ORDER BY supplier_id LIMIT 10")
    for row in cur.fetchall():
        print(f"{row[0]:>3} | {row[1]}")

    print("\n[고객 목록 일부]")
    cur.execute("SELECT customer_id, customer_name FROM CUSTOMER ORDER BY customer_id LIMIT 10")
    for row in cur.fetchall():
        print(f"{row[0]:>3} | {row[1]}")

    conn.close()


# ------------------------------------------------------------
# 1. 구매 처리
# ------------------------------------------------------------
def purchase_product() -> None:
    """
    구매 처리
    - SALES INSERT
    - SALESDETAIL INSERT
    - INVENTORY quantity 차감

    현재 버전은 CLI 단순화를 위해 한 번에 상품 1종 구매를 처리
    여러 상품 구매가 필요하면 이 함수를 반복 호출
    """
    print("\n[구매 처리]")
    show_basic_data()

    store_id = input_int("매장 ID: ", 1)
    customer_id = input_int("고객 ID: ", 1)
    product_id = input_int("상품 ID: ", 1)
    quantity = input_int("구매 수량: ", 1)

    payment_method = input("결제수단(cash/card/mobile_pay) [card]: ").strip() or "card"
    if payment_method not in {"cash", "card", "mobile_pay"}:
        print("결제수단은 cash, card, mobile_pay 중 하나여야 합니다.")
        return

    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        # 동시에 구매가 들어와도 재고 확인과 차감이 한 트랜잭션 안에서 처리되도록 잠금 시작
        cur.execute("BEGIN IMMEDIATE")

        if not row_exists(cur, "STORE", "store_id", store_id):
            raise ValueError("존재하지 않는 매장 ID입니다.")
        if not row_exists(cur, "CUSTOMER", "customer_id", customer_id):
            raise ValueError("존재하지 않는 고객 ID입니다.")
        if not row_exists(cur, "PRODUCT", "product_id", product_id):
            raise ValueError("존재하지 않는 상품 ID입니다.")

        cur.execute(
            """
            SELECT quantity, store_price
            FROM INVENTORY
            WHERE store_id = ? AND product_id = ?
            """,
            (store_id, product_id),
        )
        inv = cur.fetchone()
        if inv is None:
            raise ValueError("해당 매장에 이 상품 재고 정보가 없습니다.")

        current_quantity, store_price = inv
        if current_quantity < quantity:
            raise ValueError(f"재고가 부족합니다. 현재 재고: {current_quantity}")

        if store_price is None:
            cur.execute("SELECT base_price FROM PRODUCT WHERE product_id = ?", (product_id,))
            store_price = cur.fetchone()[0]

        total_amount = float(store_price) * quantity

        cur.execute(
            """
            INSERT INTO SALES
                (sale_datetime, total_amount, payment_method, store_id, customer_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (now_text(), total_amount, payment_method, store_id, customer_id),
        )
        sale_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO SALESDETAIL
                (sale_id, product_id, quantity, unit_price, discount_amount)
            VALUES (?, ?, ?, ?, 0)
            """,
            (sale_id, product_id, quantity, store_price),
        )

        cur.execute(
            """
            UPDATE INVENTORY
            SET quantity = quantity - ?,
                last_updated = ?
            WHERE store_id = ? AND product_id = ?
            """,
            (quantity, today_text(), store_id, product_id),
        )

        conn.commit()
        print(f"구매 처리 완료! 판매 ID: {sale_id}, 총액: {total_amount:,.0f}원")

    except Exception as e:
        conn.rollback()
        print(f"구매 처리 실패: {e}")
    finally:
        conn.close()


# ------------------------------------------------------------
# 2. 발주 처리
# ------------------------------------------------------------
def create_purchase_order() -> None:
    """
    발주 처리
    - PURCHASEORDER INSERT
    - ORDERDETAIL INSERT

    현재 버전은 한 번에 상품 1종 발주를 처리
    """
    print("\n[발주 처리]")
    show_basic_data()

    store_id = input_int("매장 ID: ", 1)
    supplier_id = input_int("공급업체 ID: ", 1)
    product_id = input_int("상품 ID: ", 1)
    order_quantity = input_int("발주 수량: ", 1)

    expected_default = (date.today() + timedelta(days=3)).isoformat()
    expected_arrival_date = input(f"예상 입고일(YYYY-MM-DD) [{expected_default}]: ").strip() or expected_default

    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        cur.execute("BEGIN")

        if not row_exists(cur, "STORE", "store_id", store_id):
            raise ValueError("존재하지 않는 매장 ID입니다.")
        if not row_exists(cur, "SUPPLIER", "supplier_id", supplier_id):
            raise ValueError("존재하지 않는 공급업체 ID입니다.")
        if not row_exists(cur, "PRODUCT", "product_id", product_id):
            raise ValueError("존재하지 않는 상품 ID입니다.")

        order_date = today_text()
        if expected_arrival_date < order_date:
            raise ValueError("예상 입고일은 발주일보다 빠를 수 없습니다.")

        cur.execute("SELECT base_price FROM PRODUCT WHERE product_id = ?", (product_id,))
        base_price = cur.fetchone()[0]
        supply_price = round(float(base_price) * 0.7) if base_price is not None else 0

        cur.execute(
            """
            INSERT INTO PURCHASEORDER
                (order_date, status, expected_arrival_date, store_id, supplier_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_date, "발주완료", expected_arrival_date, store_id, supplier_id),
        )
        order_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO ORDERDETAIL
                (order_id, product_id, order_quantity, supply_price)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, product_id, order_quantity, supply_price),
        )

        conn.commit()
        print(f"발주 처리 완료! 발주 ID: {order_id}")

    except Exception as e:
        conn.rollback()
        print(f"발주 처리 실패: {e}")
    finally:
        conn.close()


# ------------------------------------------------------------
# 3. 입고 처리
# ------------------------------------------------------------
def receive_delivery() -> None:
    """
    입고 처리
    - DELIVERY INSERT
    - INVENTORY quantity 증가
    - PURCHASEORDER status 갱신
    """
    print("\n[입고 처리]")

    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        print("\n[입고 가능한 발주 목록]")
        cur.execute(
            """
            SELECT
                po.order_id,
                po.status,
                po.store_id,
                s.store_name,
                od.product_id,
                p.product_name,
                od.order_quantity,
                COALESCE(SUM(d.delivered_quantity), 0) AS delivered_quantity
            FROM PURCHASEORDER po
            JOIN ORDERDETAIL od ON po.order_id = od.order_id
            JOIN STORE s ON po.store_id = s.store_id
            JOIN PRODUCT p ON od.product_id = p.product_id
            LEFT JOIN DELIVERY d
                ON od.order_id = d.order_id
               AND od.product_id = d.product_id
            GROUP BY po.order_id, od.product_id
            HAVING delivered_quantity < od.order_quantity
            ORDER BY po.order_id
            LIMIT 20
            """
        )
        rows = cur.fetchall()
        if not rows:
            print("입고 처리할 수 있는 미완료 발주가 없습니다.")
            return

        for row in rows:
            remaining = row[6] - row[7]
            print(
                f"발주ID {row[0]:>3} | 상품ID {row[4]:>3} | {row[5]} | "
                f"주문 {row[6]} / 입고 {row[7]} / 남은 수량 {remaining}"
            )

        order_id = input_int("입고 처리할 발주 ID: ", 1)
        product_id = input_int("입고 처리할 상품 ID: ", 1)
        delivered_quantity = input_int("입고 수량: ", 1)

        cur.execute("BEGIN IMMEDIATE")

        cur.execute(
            """
            SELECT po.store_id, od.order_quantity,
                   COALESCE(SUM(d.delivered_quantity), 0) AS already_delivered
            FROM PURCHASEORDER po
            JOIN ORDERDETAIL od ON po.order_id = od.order_id
            LEFT JOIN DELIVERY d
                ON od.order_id = d.order_id
               AND od.product_id = d.product_id
            WHERE od.order_id = ? AND od.product_id = ?
            GROUP BY po.store_id, od.order_quantity
            """,
            (order_id, product_id),
        )
        order_info = cur.fetchone()
        if order_info is None:
            raise ValueError("해당 발주/상품 조합이 없습니다.")

        store_id, order_quantity, already_delivered = order_info
        remaining_quantity = order_quantity - already_delivered
        if delivered_quantity > remaining_quantity:
            raise ValueError(f"입고 수량이 남은 발주 수량보다 많습니다. 남은 수량: {remaining_quantity}")

        cur.execute(
            """
            INSERT INTO DELIVERY
                (delivery_datetime, delivered_quantity, order_id, product_id)
            VALUES (?, ?, ?, ?)
            """,
            (now_text(), delivered_quantity, order_id, product_id),
        )
        delivery_id = cur.lastrowid

        # 재고 행이 있으면 증가, 없으면 새로 생성
        cur.execute(
            """
            SELECT 1
            FROM INVENTORY
            WHERE store_id = ? AND product_id = ?
            """,
            (store_id, product_id),
        )
        if cur.fetchone():
            cur.execute(
                """
                UPDATE INVENTORY
                SET quantity = quantity + ?,
                    last_updated = ?
                WHERE store_id = ? AND product_id = ?
                """,
                (delivered_quantity, today_text(), store_id, product_id),
            )
        else:
            cur.execute(
                "SELECT base_price FROM PRODUCT WHERE product_id = ?",
                (product_id,),
            )
            base_price = cur.fetchone()[0]
            store_price = round(float(base_price) * 1.2) if base_price is not None else 0
            cur.execute(
                """
                INSERT INTO INVENTORY
                    (store_id, product_id, quantity, safety_stock, last_updated, store_price)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (store_id, product_id, delivered_quantity, 10, today_text(), store_price),
            )

        new_total_delivered = already_delivered + delivered_quantity
        new_status = "입고완료" if new_total_delivered >= order_quantity else "부분입고"
        cur.execute(
            "UPDATE PURCHASEORDER SET status = ? WHERE order_id = ?",
            (new_status, order_id),
        )

        conn.commit()
        print(f"입고 처리 완료! 입고 ID: {delivery_id}, 발주 상태: {new_status}")

    except Exception as e:
        conn.rollback()
        print(f"입고 처리 실패: {e}")
    finally:
        conn.close()


# ------------------------------------------------------------
# 4. 자동 재주문 발주
# ------------------------------------------------------------
def auto_reorder() -> None:
    """
    안전재고 이하 상품 자동 발주
    - INVENTORY.quantity <= INVENTORY.safety_stock 상품 조회
    - PURCHASEORDER / ORDERDETAIL 생성
    """
    print("\n[자동 재주문 발주]")

    supplier_id = input_int("자동 발주에 사용할 공급업체 ID: ", 1)
    expected_default = (date.today() + timedelta(days=3)).isoformat()
    expected_arrival_date = input(f"예상 입고일(YYYY-MM-DD) [{expected_default}]: ").strip() or expected_default

    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        cur.execute("BEGIN")

        if not row_exists(cur, "SUPPLIER", "supplier_id", supplier_id):
            raise ValueError("존재하지 않는 공급업체 ID입니다.")

        cur.execute(
            """
            SELECT i.store_id, i.product_id, i.quantity, i.safety_stock, p.base_price
            FROM INVENTORY i
            JOIN PRODUCT p ON i.product_id = p.product_id
            WHERE i.quantity <= i.safety_stock
            ORDER BY i.store_id, i.product_id
            """
        )
        low_stock_items = cur.fetchall()

        if not low_stock_items:
            print("안전재고 이하 상품이 없습니다.")
            conn.rollback()
            return

        order_date = today_text()
        if expected_arrival_date < order_date:
            raise ValueError("예상 입고일은 발주일보다 빠를 수 없습니다.")

        created_orders: dict[int, int] = {}
        created_detail_count = 0

        for store_id, product_id, quantity, safety_stock, base_price in low_stock_items:
            if store_id not in created_orders:
                cur.execute(
                    """
                    INSERT INTO PURCHASEORDER
                        (order_date, status, expected_arrival_date, store_id, supplier_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (order_date, "발주완료", expected_arrival_date, store_id, supplier_id),
                )
                created_orders[store_id] = cur.lastrowid

            order_id = created_orders[store_id]
            # 안전재고의 3배 수준까지 채우도록 발주 수량 계산, 최소 10개
            target_quantity = max(safety_stock * 3, 20)
            order_quantity = max(target_quantity - quantity, 10)
            supply_price = round(float(base_price) * 0.7) if base_price is not None else 0

            cur.execute(
                """
                INSERT INTO ORDERDETAIL
                    (order_id, product_id, order_quantity, supply_price)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, product_id, order_quantity, supply_price),
            )
            created_detail_count += 1

        conn.commit()
        print(f"자동 발주 완료! 발주 {len(created_orders)}건, 발주 상세 {created_detail_count}건 생성")

    except Exception as e:
        conn.rollback()
        print(f"자동 발주 실패: {e}")
    finally:
        conn.close()


# ------------------------------------------------------------
# 메뉴
# ------------------------------------------------------------
def transaction_menu() -> None:
    while True:
        print("\n==============================")
        print("구매 / 발주 / 입고 관리")
        print("==============================")
        print("1. 구매 처리")
        print("2. 발주 처리")
        print("3. 입고 처리")
        print("4. 자동 재주문 발주")
        print("5. 참고 ID 목록 보기")
        print("0. 이전 메뉴로 돌아가기")

        choice = input("메뉴 선택: ").strip()

        if choice == "1":
            purchase_product()
        elif choice == "2":
            create_purchase_order()
        elif choice == "3":
            receive_delivery()
        elif choice == "4":
            auto_reorder()
        elif choice == "5":
            show_basic_data()
        elif choice == "0":
            break
        else:
            print("잘못된 입력입니다. 다시 선택해주세요.")


if __name__ == "__main__":
    transaction_menu()
