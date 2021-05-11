import time
import hashlib
import json
import requests
import base64
from flask import Flask, request
from multiprocessing import Process, Pipe
import ecdsa
from flask_cors import CORS

from miner1_config import MINER_ADDRESS, MINER_NODE_URL, PEER_NODES

node = Flask(__name__)
CORS(node)
class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        """Returns a new Block object. Each block is "chained" to its previous
        by calling its unique hash.

        Arguments:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.
            hash(str): Current block unique hash.
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.hash_block()

    def hash_block(self):
        """Each block is hashed twice using SHA-256 cryptographic hashing"""
        sha = hashlib.sha256()
        sha.update((str(self.index) + str(self.timestamp) + str(self.data) + str(self.previous_hash)).encode('utf-8'))
        return sha.hexdigest()

def create_genesis_block():
    """The blockchain must be initialized with a genesis block,
        manually filled in with random values"""
    return Block(0, time.time(), {
        "proof-of-work": 9,
        "transactions": None},
        "0")

# Node's blockchain copy
BLOCKCHAIN = [create_genesis_block()]

#This Node's Mempool of unprocessed transactions
NODE_PENDING_TRANSACTIONS = []

def proof_of_work(last_proof, blockchain):
    # Creates a variable that we will use to find our next proof of work
    incrementer = last_proof + 1
    # Keep incrementing the incrementer until it's equal to a number divisible by 9
    # and the proof of work of the previous block in the chain
    start_time = time.time()
    while not (incrementer % 7919 == 0 and incrementer % last_proof == 0):
        incrementer += 1
        # Check if any node found the solution every 60 seconds
        if int((time.time()-start_time) % 60) == 0:
            # If any other node got the proof, stop searching
            new_blockchain = consensus(blockchain)
            if new_blockchain:
                # (False: another node got proof first, new blockchain)
                return False, new_blockchain
    # Once that number is found, we can return it as a proof of our work
    return incrementer, blockchain


def mine(a, blockchain):
    """Mining is the only way that new coins can be created.
    In order to prevent too many coins to be created, the process
    is slowed down by the proof of work algorithm.
    """
    BLOCKCHAIN = blockchain
    while True:
        # Load all pending transactions sent to the node server

        NODE_PENDING_TRANSACTIONS = a.recv()
        #Check pipe buffer for a request for the entire blockchain by the parent thread
        if NODE_PENDING_TRANSACTIONS == "get_blockchain":
            a.send(BLOCKCHAIN)
            continue

        '''# Get the previous block's proof of work
        last_block = BLOCKCHAIN[-1]
        last_proof = last_block.data['proof-of-work']
        # Calculate the proof of work for the current block being mined
        #Program will hang here until the correct proof of work is found
        proof = proof_of_work(last_proof, BLOCKCHAIN)'''
        #get the proof of work from the parent process
        proof, BLOCKCHAIN = a.recv()
        # If another node found the proof_of_work before us, start mining again
        if not proof[0]:
            # Update blockchain and save it to file
            BLOCKCHAIN = proof[1]
            a.send(BLOCKCHAIN)
            continue
        else:
            # Once we find a valid proof of work, we know we can mine a block so
            # Add a transaction that rewards the miner with some coins
            last_block = BLOCKCHAIN[-1]
            last_proof = last_block.data['proof-of-work']
            NODE_PENDING_TRANSACTIONS.append({
                "from": "network",
                "to": MINER_ADDRESS,
                "amount": 1})
            # Gather data for the new block
            new_block_data = {
                "proof-of-work": proof[0],
                "transactions": list(NODE_PENDING_TRANSACTIONS)
            }
            new_block_index = last_block.index + 1
            new_block_timestamp = time.time()
            last_block_hash = last_block.hash
            # Purge the unprocessed transaction list
            NODE_PENDING_TRANSACTIONS = []
            # Now create the new block
            mined_block = Block(new_block_index, new_block_timestamp, new_block_data, last_block_hash)
            #add block to blockchain
            BLOCKCHAIN.append(mined_block)
            print("new blockchain length: ", len(BLOCKCHAIN))
            #Display the new block
            print(json.dumps({
              "index": new_block_index,
              "timestamp": str(new_block_timestamp),
              "data": new_block_data,
              "hash": last_block_hash
            }) + "\n")


def find_new_chains():
    # Get the blockchains of every other node
    other_chains = []
    for node_url in PEER_NODES:
        # Get their chains using a GET request
        headers = headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
        chain = requests.get(url = "http://localhost:5000/blocks", headers=headers).content
        # Convert each block in the blockchain from JSON to Python Dictionaries
        chain = json.loads(chain)
        #convert each block in the blockchain from dicts to Block objects
        reformatted_chain = []
        for block in chain:
            curr_block = Block(block["index"], block["timestamp"], block["data"], block["previous_hash"])
            curr_block.hash = block["hash"]
            reformatted_chain.append(curr_block)
        print("Length of other chain: ", len(reformatted_chain))
        # Verify other node block is correct
        validated = validate_blockchain(reformatted_chain)
        if validated:
            # Add it to our list
            other_chains.append(reformatted_chain)
    return other_chains


def consensus(blockchain):
    # Get the blocks from other nodes
    other_chains = find_new_chains()
    # If our chain isn't longest, then we store the longest chain
    BLOCKCHAIN = blockchain
    longest_chain = BLOCKCHAIN
    for chain in other_chains:
        if len(longest_chain) < len(chain):
            longest_chain = chain
    # If the longest chain wasn't ours, then we set our chain to the longest
    if longest_chain == BLOCKCHAIN:
        # Keep searching for proof
        return False
    else:
        # Give up searching proof, update chain and start over again
        BLOCKCHAIN = longest_chain
        return BLOCKCHAIN


def validate_blockchain(block):
    """Validate the submitted chain. If hashes are not correct, return false
    block(str): json
    """
    return True


@node.route('/blocks', methods=['GET'])
def get_blocks():
    # Request the full blockchain from the child process
    b.send("get_blockchain")
    BLOCKCHAIN = b.recv()
    chain_to_send = BLOCKCHAIN
    # Converts our blocks into dictionaries so we can send them as json objects later
    chain_to_send_json = []
    for block in chain_to_send:
        block = {
            "index": block.index,
            "timestamp": block.timestamp,
            "data": block.data,
            "previous_hash": block.previous_hash,
            "hash": block.hash
        }
        chain_to_send_json.append(block)
    #convert blocks to json
    chain_to_send = json.dumps(chain_to_send_json)
    return chain_to_send


@node.route('/txion', methods=['GET', 'POST'])
def transaction():
    """Each transaction sent to this node gets validated and submitted.
    Then it waits to be added to the blockchain. Transactions only move
    coins, they don't create it.
    """
    if request.method == 'POST':
        # On each new POST request, we extract the transaction data
        new_txion = request.get_json()
        # Add transaction to the pending transaction list
        if validate_signature(new_txion['from'], new_txion['signature'], new_txion['message']):
            NODE_PENDING_TRANSACTIONS.append(new_txion)
            # Because the transaction was successfully submitted, log it to the console
            print("New transaction")
            print("FROM: {0}".format(new_txion['from']))
            print("TO: {0}".format(new_txion['to']))
            print("AMOUNT: {0}\n".format(new_txion['amount']))
            # Then we let the client know it worked out
            """
            Have the Parent process retreive other node's blockchains, verify them, and choose the longest one.
            Then, pipe the correct blockchain back down to the child
            """
            # Request the full blockchain from the child process
            b.send("get_blockchain")
            BLOCKCHAIN = b.recv()
            # Get the previous block's proof of work
            last_block = BLOCKCHAIN[-1]
            last_proof = last_block.data['proof-of-work']
            #calculate the proof-of-work
            proof = proof_of_work(last_proof, BLOCKCHAIN)
            #send pending transactions and proof of work
            b.send(NODE_PENDING_TRANSACTIONS)
            b.send([proof, BLOCKCHAIN])
            return "Transaction submission successful\n"
        else:
            return "Transaction submission failed. Wrong signature\n"
    # Send pending transactions to the child process to be mined
    elif request.method == 'GET':
        pending = json.dumps(NODE_PENDING_TRANSACTIONS)
        # Empty transaction list
        NODE_PENDING_TRANSACTIONS[:] = []
        return pending


def validate_signature(public_key, signature, message):
    """Verifies if the signature is correct. This is used to prove
    it's you (and not someone else) trying to do a transaction with your
    address. Called when a user tries to submit a new transaction.
    """
    public_key = (base64.b64decode(public_key)).hex()
    signature = base64.b64decode(signature)
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
    # Try changing into an if/else statement as except is too broad.
    try:
        return vk.verify(signature, message.encode())
    except:
        return False


def welcome_msg():
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


if __name__ == '__main__':
    welcome_msg()
    # Start mining
    a, b = Pipe()
    p1 = Process(target=mine, args=(a, BLOCKCHAIN))
    p1.start()
    # Start server to receive transactions
    p2 = Process(target=node.run(port=5001), args=b)
    p2.start()
