import argparse
import sqlite3
import os
from datetime import date

from dotenv import load_dotenv
from algosdk import account, algod, transaction

parser = argparse.ArgumentParser(description="ChatWall CLI")

load_dotenv()

conn = sqlite3.connect("chatwall.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS accounts (private_key TEXT, address TEXT);")

acl = algod.AlgodClient(os.getenv("API_TOKEN"), os.getenv("API_ADDRESS"))
sp = acl.suggested_params()

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
    note = message.encode()
    amount = 0
    txn = transaction.PaymentTxn(account.address_from_private_key(from_addr), sp["fee"], sp["lastRound"],
                                 sp["lastRound"] + 500, sp['genesishashb64'],
                                 to_addr, amount, note=note)

    # Sign transaction
    stx = txn.sign(private_key)

    return stx


def get_messages(to_addr, first=None, last=None, from_date=None, to_date=None):
    return acl.transactions_by_address(to_addr, first, last, from_date, to_date)


if __name__ == '__main__':
    parser.add_argument('-m', '--message', metavar='msg', type=str, help='message to be sent.')
    parser.add_argument('-t', '--to_address', metavar='addr', type=str, help='address to be sent to.')
    parser.add_argument('-f', '--from_address', action='store_true', help='print the address used to send and receive '
                                                                          'messages.')
    parser.add_argument('-r', '--read_messages', action='store_true', help='print messages sent to you.')
    args = parser.parse_args()

    # Get account
    (private_key, address) = get_or_gen_account()

    # Print the users public key if the -f flag is used
    if args.from_address:
        print(address)
        exit(0)

    if args.read_messages:
        messages = None
        try:
            messages = get_messages(address, first=sp['lastRound'] - 1000, last=sp['lastRound'])
        except:
            pass

        print(messages)
        exit(0)

    message = args.message

    # Generate the signed transaction
    txn = txn_message_to(private_key, message, args.to_address)

    # Send transaction over the network
    txid = acl.send_transaction(txn)

    print(f'"{message}" sent to {address}')
    print("Transaction ID: ", txid)

conn.close()
