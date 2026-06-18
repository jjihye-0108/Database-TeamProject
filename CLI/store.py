from db import get_connection


def store_menu():
    while True:
        print("\n===== 매장 조회 =====")
        print("1. 전체 매장 조회")
        print("2. 특정 매장 조회")
        print("0. 이전 메뉴")

        choice = input("\n선택 > ")

        conn = get_connection()
        cur = conn.cursor()

        if choice == "1":

            cur.execute("""
                SELECT
                    store_id,
                    store_name,
                    address,
                    phone,
                    opening_hours
                FROM STORE
                ORDER BY store_id
            """)

            rows = cur.fetchall()

            print("\n===== 전체 매장 목록 =====")

            for row in rows:
                print(
                    f"[{row['store_id']}] "
                    f"{row['store_name']} | "
                    f"{row['phone']} | "
                    f"{row['opening_hours']}"
                )

        elif choice == "2":

            store_id = input("매장 ID 입력 > ")

            cur.execute("""
                SELECT
                    store_id,
                    store_name,
                    address,
                    phone,
                    opening_hours
                FROM STORE
                WHERE store_id = ?
            """, (store_id,))

            row = cur.fetchone()

            if row is None:
                print("해당 매장이 존재하지 않습니다.")

            else:
                print("\n===== 매장 정보 =====")
                print(f"매장 ID : {row['store_id']}")
                print(f"매장명 : {row['store_name']}")
                print(f"주소 : {row['address']}")
                print(f"전화번호 : {row['phone']}")
                print(f"영업시간 : {row['opening_hours']}")

        elif choice == "0":
            conn.close()
            return

        else:
            print("잘못된 입력입니다.")

        conn.close()