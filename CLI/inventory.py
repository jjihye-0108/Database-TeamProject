from db import get_connection


def inventory_menu():
    while True:
        print("\n===== 재고 조회 =====")
        print("1. 매장별 재고 조회")
        print("2. 재고 부족 상품 조회")
        print("0. 이전 메뉴")

        choice = input("\n선택 > ")

        if choice == "1":
            store_id = input("매장 ID 입력 > ")
            show_inventory_by_store(store_id)

        elif choice == "2":
            show_low_stock()

        elif choice == "0":
            return

        else:
            print("잘못된 입력입니다.")


def show_inventory_by_store(store_id):
    conn = get_connection()
    cur = conn.cursor()

    # [수정] 매장 자체가 없는 경우와, 매장은 있지만 재고가 0건인 경우를 구분
    cur.execute(
        "SELECT 1 FROM STORE WHERE store_id = ?",
        (store_id,),
    )
    if cur.fetchone() is None:
        print("해당 매장이 존재하지 않습니다.")
        conn.close()
        return

    cur.execute("""
        SELECT
            p.product_id,
            p.product_name,
            i.quantity,
            i.safety_stock
        FROM INVENTORY i
        JOIN PRODUCT p
            ON i.product_id = p.product_id
        WHERE i.store_id = ?
        ORDER BY p.product_id
    """, (store_id,))

    rows = cur.fetchall()

    if not rows:
        print("해당 매장의 재고 정보가 없습니다.")
    else:
        print("\n[매장 재고]")
        print("-" * 60)

        # [수정] sqlite3.Row는 컬럼명으로 접근 (db.py에서 row_factory = sqlite3.Row 설정됨)
        for row in rows:
            print(
                f"상품ID: {row['product_id']:<3} | "
                f"{row['product_name']:<25} | "
                f"재고: {row['quantity']:<4} | "
                f"안전재고: {row['safety_stock']}"
            )

    conn.close()


def show_low_stock():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            i.store_id,
            p.product_name,
            i.quantity,
            i.safety_stock
        FROM INVENTORY i
        JOIN PRODUCT p
            ON i.product_id = p.product_id
        WHERE i.quantity <= i.safety_stock
        ORDER BY i.store_id
    """)

    rows = cur.fetchall()

    if not rows:
        print("재고 부족 상품이 없습니다.")
    else:
        print("\n[재고 부족 상품]")
        print("-" * 70)

        # [수정] sqlite3.Row는 컬럼명으로 접근
        for row in rows:
            print(
                f"매장ID: {row['store_id']:<3} | "
                f"{row['product_name']:<25} | "
                f"재고: {row['quantity']:<4} | "
                f"안전재고: {row['safety_stock']}"
            )

    conn.close()