from core.db import init_db, DB_PATH
from wallet.crypto import WalletManager

def main():
    print("=== Wallet Manager ===")
    init_db(DB_PATH)
    wallet = WalletManager(db_path=DB_PATH)
    addr = wallet.get_address()
    if addr:
        print(f"Wallet address: {addr}")
    else:
        print("No wallet configured. Set wallet_address in config.")
    print("Done.")

if __name__ == "__main__":
    main()
