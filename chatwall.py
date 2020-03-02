import sqlite3
import os
from dotenv import load_dotenv
from algosdk import account, algod, transaction

load_dotenv()

conn = sqlite3.connect("chatwall.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS accounts (private_key TEXT, address TEXT);")

acl = algod.AlgodClient(os.getenv("API_TOKEN"), os.getenv("API_ADDRESS"))

if __name__ == '__main__':

    res = c.execute("SELECT private_key, address FROM accounts;").fetchone()
    private_key = None
    address = None

    # if private_key is None or address is None:
    if res is None:
        # generate an account
        private_key, address = account.generate_account()

        c.execute("INSERT INTO accounts (private_key, address) VALUES (?, ?)", (private_key, address))
        conn.commit()
    else:
        private_key = res[0]
        address = res[1]

    sp = acl.suggested_params()

    note = "Hello Algorand!".encode()
    amount = 0
    txn = transaction.PaymentTxn(address, sp["fee"], sp["lastRound"], sp["lastRound"] + 500, sp['genesishashb64'], address, amount, note=note)

    # Sign transaction
    stx = txn.sign(private_key)

    # Send transaction
    txid = acl.send_transaction(stx)

    print("Transaction ID: ", txid)

conn.close()
