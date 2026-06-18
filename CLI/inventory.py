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
        print("해당 매장이 존재하지 않거나 재고 정보가 없습니다.")
    else:
        print("\n[매장 재고]")
        print("-" * 60)

        for pid, name, qty, safety in rows:
            print(
                f"상품ID: {pid:<3} | "
                f"{name:<25} | "
                f"재고: {qty:<4} | "
                f"안전재고: {safety}"
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

        for store_id, product, qty, safety in rows:
            print(
                f"매장ID: {store_id:<3} | "
                f"{product:<25} | "
                f"재고: {qty:<4} | "
                f"안전재고: {safety}"
            )

    conn.close()