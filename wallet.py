"""This is going to be your wallet. Here you can do several things:
- Generate a new address (public and private key). You are going
to use this address (public key) to send or receive any transactions. You can
have as many addresses as you wish, but keep in mind that if you
lose its credential data, you will not be able to retrieve it.

- Send coins to another address
- Retrieve the entire blockchain and check your balance

If this is your first time using this script don't forget to generate
a new address and edit miner config file with it (only if you are
going to mine).

Timestamp in hashed message. When you send your transaction it will be received
by several nodes. If any node mine a block, your transaction will get added to the
blockchain but other nodes still will have it pending. If any node see that your
transaction with same timestamp was added, they should remove it from the
node_pending_transactions list to avoid it get processed more than 1 time.
"""

import requests
import time
import base64
import ecdsa
import json

PEER_NODES = ["http://localhost:5002", "http://localhost:5001", "http://localhost:5000"]
def wallet():
    response = None
    while response not in ["1", "2", "3"]:
        response = input("""What do you want to do?
        1. Generate new wallet
        2. Send coins to another wallet
        3. View Blockchain\n""")
    if response == "1":
        # Generate new wallet
        print("""=========================================\n
IMPORTANT: save this credentials or you won't be able to recover your wallet\n
=========================================\n""")
        generate_ECDSA_keys()
    elif response == "2":
        addr_from = input("From: introduce your wallet address (public key)\n")
        private_key = input("Introduce your private key\n")
        addr_to = input("To: introduce destination wallet address\n")
        amount = input("Amount: number stating how much do you want to send\n")
        print("=========================================\n\n")
        print("Is everything correct?\n")
        print("From: {0}\nPrivate Key: {1}\nTo: {2}\nAmount: {3}\n".format(addr_from, private_key, addr_to, amount))
        response = input("y/n\n")
        if response.lower() == "y":
            send_transaction(addr_from, private_key, addr_to, amount)
    else:  # Will always occur when response == 3.
        view_blockchain()


def send_transaction(addr_from, private_key, addr_to, amount):
    """Sends your transaction to different nodes. Once any of the nodes manage
    to mine a block, your transaction will be added to the blockchain. Despite
    that, there is a low chance your transaction gets canceled due to other nodes
    having a longer chain. So make sure your transaction is deep into the chain
    before claiming it as approved!
    """
    #For fast debugging REMOVE LATER
    private_key="9b02a80c0a7a0773a2f13e355867ccfd99f609610e66c6ada87c08b76878f5ea"
    amount="3000"
    addr_from="WC1Z3SKJyZDyuHHemTENPJRwHF66K07PobksDg6x51Ej5DcuEPueBoQOODhAnkaQ3JuXtDjXybLhFffSlgx42A=="
    addr_to="FNyTxLATyboflAcbcSwKzOIno/26/tMS8Ga1oMr3vMd5ijW3RrU1Sqb8WJUp+JgwJkXtaVvil0qfQ9eX2sT1Ng=="

    if len(private_key) == 64:
        signature, message = sign_ECDSA_msg(private_key)
        payload = {"from": addr_from,
                   "to": addr_to,
                   "amount": amount,
                   "signature": signature.decode(),
                   "message": message}
        headers = {"Content-Type": "application/json"}
        #broadcast transaction to the network
        for url in PEER_NODES:
            res = requests.post(url+'/txion', json=payload, headers=headers)
            if url == PEER_NODES[0]:
                print(res.text)
    else:
        print("Wrong address or key length! Verify and try again.")


def view_blockchain():
    """Retrieve the entire blockchain. With this you can check your
    wallets balance. If the blockchain is to long, it may take some time to load.
    """
    max_blockchain_length = 0
    blockchain = None
    for url in PEER_NODES:
        res = requests.get(url+'/blocks')
        chain_length = len(json.loads(res.text))
        if max_blockchain_length < chain_length:
            max_blockchain_length = chain_length
            blockchain = res.text
    print("-----------------------------------")
    print("Blockchain Length: ", max_blockchain_length)
    print("-----------------------------------")
    print(blockchain)
def generate_ECDSA_keys():
    """This function takes care of creating your private and public (your address) keys.
    It's very important you don't lose any of them or those wallets will be lost
    forever. If someone else get access to your private key, you risk losing your coins.

    private_key: str
    public_ley: base64 (to make it shorter)
    """
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1) #this is your sign (private key)
    private_key = sk.to_string().hex() #convert your private key to hex
    vk = sk.get_verifying_key() #this is your verification key (public key)
    public_key = vk.to_string().hex()
    #we are going to encode the public key to make it shorter
    public_key = base64.b64encode(bytes.fromhex(public_key))

    filename = input("Write the name of your new address: ") + ".txt"
    with open(filename, "w") as f:
        f.write("Private key: {0}\nWallet address / Public key: {1}".format(private_key, public_key.decode()))
    print("Your new address and private key are now in the file {0}".format(filename))

def sign_ECDSA_msg(private_key):
    """Sign the message to be sent
    private_key: must be hex

    return
    signature: base64 (to make it shorter)
    message: str
    """
    # Get timestamp, round it, make it into a string and encode it to bytes
    message = str(round(time.time()))
    bmessage = message.encode()
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = base64.b64encode(sk.sign(bmessage))
    return signature, message


if __name__ == '__main__':
    print("""=================================================================================\n
.oooooo..o oooo                  oooo          .oooooo.              o8o
d8P'    `Y8 `888                  `888         d8P'  `Y8b             `"'
Y88bo.       888 .oo.    .oooo.    888 .oo.   888           .ooooo.  oooo  ooo. .oo.
 `"Y8888o.   888P"Y88b  `P  )88b   888P"Y88b  888          d88' `88b `888  `888P"Y88b
     `"Y88b  888   888   .oP"888   888   888  888          888   888  888   888   888
oo     .d8P  888   888  d8(  888   888   888  `88b    ooo  888   888  888   888   888
8""88888P'  o888o o888o `Y888""8o o888o o888o  `Y8bood8P'  `Y8bod8P' o888o o888o o888o



 v1 - BLOCKCHAIN SYSTEM\n
===================================================================================\n\n
""")
    wallet()
    input("Press ENTER to exit...")
