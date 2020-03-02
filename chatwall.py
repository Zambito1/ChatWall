import sqlite3
import os
from dotenv import load_dotenv
from algosdk import account, algod, transaction

load_dotenv()

conn = sqlite3.connect("chatwall.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS accounts (private_key TEXT, address TEXT);")

acl = algod.AlgodClient(os.getenv("API_TOKEN"), os.getenv("API_ADDRESS"))


def get_or_gen_account():
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

    return (private_key, address)


def txn_message_to(from_addr, message, to_addr):
    sp = acl.suggested_params()

    note = message.encode()
    amount = 0
    txn = transaction.PaymentTxn(account.address_from_private_key(from_addr), sp["fee"], sp["lastRound"], sp["lastRound"] + 500, sp['genesishashb64'],
                                 to_addr, amount, note=note)

    # Sign transaction
    stx = txn.sign(private_key)

    return stx


if __name__ == '__main__':

    # Get account
    (private_key, address) = get_or_gen_account()

    message = "Hello world!"

    # Generate the signed transaction
    txn = txn_message_to(private_key, message, address)

    # Send transaction over the network
    txid = acl.send_transaction(txn)

    print(f'"{message}" sent to {address}')
    print("Transaction ID: ", txid)

conn.close()
