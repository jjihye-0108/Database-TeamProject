from db import get_connection


def product_menu():
    while True:
        print("\n===== 상품 조회 =====")
        print("1. 전체 상품 조회")
        print("2. 상품명 검색")
        print("3. 브랜드별 조회")
        print("0. 이전 메뉴")

        choice = input("\n선택 > ")

        conn = get_connection()
        cur = conn.cursor()

        if choice == "1":

            cur.execute("""
                SELECT
                    p.product_id,
                    p.product_name,
                    b.brand_name,
                    p.base_price
                FROM PRODUCT p
                JOIN BRAND b
                    ON p.brand_id = b.brand_id
                ORDER BY p.product_id
            """)

            rows = cur.fetchall()

            print("\n===== 전체 상품 목록 =====")
            for row in rows:
                print(
                    f"[{row['product_id']}] "
                    f"{row['product_name']} | "
                    f"{row['brand_name']} | "
                    f"{row['base_price']}원"
                )

        elif choice == "2":

            keyword = input("상품명 입력 > ")

            cur.execute("""
                SELECT
                    p.product_id,
                    p.product_name,
                    b.brand_name,
                    p.base_price
                FROM PRODUCT p
                JOIN BRAND b
                    ON p.brand_id = b.brand_id
                WHERE p.product_name LIKE ?
            """, (f"%{keyword}%",))

            rows = cur.fetchall()

            print(f"\n===== '{keyword}' 검색 결과 =====")

            if not rows:
                print("검색 결과가 없습니다.")
            else:
                for row in rows:
                    print(
                        f"[{row['product_id']}] "
                        f"{row['product_name']} | "
                        f"{row['brand_name']} | "
                        f"{row['base_price']}원"
                    )

        elif choice == "3":

            brand = input("브랜드명 입력 > ")

            cur.execute("""
                SELECT
                    p.product_id,
                    p.product_name,
                    b.brand_name,
                    p.base_price
                FROM PRODUCT p
                JOIN BRAND b
                    ON p.brand_id = b.brand_id
                WHERE b.brand_name LIKE ?
            """, (f"%{brand}%",))

            rows = cur.fetchall()

            print(f"\n===== 브랜드 '{brand}' 상품 =====")

            if not rows:
                print("해당 브랜드 상품이 없습니다.")
            else:
                for row in rows:
                    print(
                        f"[{row['product_id']}] "
                        f"{row['product_name']} | "
                        f"{row['base_price']}원"
                    )

        elif choice == "0":
            conn.close()
            return

        else:
            print("잘못된 입력입니다.")

        conn.close()