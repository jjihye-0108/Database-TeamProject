from product import product_menu
from inventory import inventory_menu
from store import store_menu

# 팀원 담당
# from purchase import purchase_menu
# from order import order_menu
# from delivery import delivery_menu


def main():
    while True:
        print("\n==============================")
        print(" 편의점 관리 시스템 ")
        print("==============================")
        print("1. 상품 조회")
        print("2. 재고 조회")
        print("3. 매장 조회")
        print("4. 구매")
        print("5. 발주")
        print("6. 입고")
        print("0. 종료")

        choice = input("\n메뉴 선택 > ")

        if choice == "1":
            product_menu()

        elif choice == "2":
            inventory_menu()

        elif choice == "3":
            store_menu()

        elif choice == "4":
            print("구매 기능 준비 중")

        elif choice == "5":
            print("발주 기능 준비 중")

        elif choice == "6":
            print("입고 기능 준비 중")

        elif choice == "0":
            print("프로그램 종료")
            break

        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    main()