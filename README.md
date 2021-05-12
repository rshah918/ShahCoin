# ShahCoin
I scratch implemented my own Cryptocurrency. ShahCoin uses modular arithmetic based Proof-of-Work, and Bitcoin's consensus mechanism. 

# Motivation
My goal is to gain a first-principles understanding of Blockchain technology. _"What I cannot create, I do not understand"-Richard Feynman_

# How to run it
1) First, install all the dependencies in requirements.txt  
`pip3 install -r requirements.txt`
2) In one terminal window, run "Wallet.py". This is your ShahCoin wallet. From here, you can generate a new wallet, make a transaction, or view the Blockchain   `python3 wallet.py`
3) Choose option 1. This will create a text file containing your wallet's private key and address. 
4) Open 3 terminal windows, and run "miner1.py", "miner2.py", and "miner3.py". These are mining nodes which will process your transaction and add it to the blockchain.  
`python3 miner1.py` `python3 miner2.py` `python3 miner3.py`
5) In your first terminal window, run "wallet.py" and choose option 2 to make a transaction. You will need to repeat steps 3 and 4 to create a destination wallet.
6) Observe the consensus algorithm in real time as nodes work to agree on one view of the Blockchain

# How it works

## Miner.py
The mining nodes have 2 processes. The parent process is a Flask server that manages all incoming/outgoing connections from the node. The child process takes care of mining additional ShahCoin and adding it to the Blockchain. Communication within a node is done via an IPC pipe, while communication across the network is done via GET/POST requests.  
ShahCoin uses a modular arithmetic based proof of work to limit the generation of new ShahCoin. This is unlike Bitcoin's proof of work.  

## Wallet.py
The wallet is where you can make transactions or view the blockchain. You need mining node to process your transactions, so make sure that "miner.py" is running in another terminal window. Transactions are not verified at the time of writing, so you can make arbitrary transactions and send ShahCoin that you do not have. This will be fixed in a future update. 
