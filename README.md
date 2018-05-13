# Blockchain Node and Wallet

This code is written with the help of one blockchain tutorial and one wallet source code. I recommend to read the tutorial to understand the most of the parts of this project.
Source1: https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
Source2: https://github.com/cosme12/SimpleCoin

## Features

* `Chain Validation (from Source1)`
* `Proof Validation (from Source1)`
* `Transaction Validation`
* `Balance Validation`
* `Signature Validation (from Source2)`
* `A proof of work algorithm (from Source1)`
* `A concensus algorithm (from Source1)`
* `Auto connecting and syncing to the system`
* `Auto saving to and loading chain from filesystem`
* `Introducing self to system when joined as a node`
* `Notifying other nodes to update their chains when mined a block`
* `Simple wallet user interface (with tkinter) that generates wallet, shows balance and make transactions`
* `Elliptic Curve Digital Signature Algorithm for secure transactions (from Source2)`

## Summary
I've made this project to understand how bitcoin and blockchain works. I've tried to build a functioning and secure blockchain system. You may find some security vulnerabilities or some bugs if you dig deep (or maybe without the need of digging deep). Anyway, I couldn't find a simple and complete blockchain code on the net so I've combined two incomplete implementations and filled the blanks on my own. I hope it helps you to understand bitcoin and blockchain system as well as it helped me. Enjoy it!

## Installation

1. Make sure [Python 3.6+](https://www.python.org/downloads/) is installed. 
2. Install [pipenv](https://github.com/kennethreitz/pipenv). 

```
$ pip install pipenv 
```

3. Create a _virtual environment_ and specify the location of your python.exe 

```
$ pipenv --python C:\Users\[USER]\AppData\Local\Programs\Python\Python36-32\python.exe
```

4. Install requirements.  

```
$ pipenv install -r requirements.txt
``` 


    
## Usage Example
1. After you've followed the steps in * *Installation* * part, run **wallet_ui.py**
```
$ pipenv run pythun wallet_ui.py
``` 

2. Generate a wallet to use as your node's wallet.
![generate_wallet](https://www.dropbox.com/s/x7d5epvfccal5zr/1.png?raw=1 "Generate a new wallet")

3. Run the server:
    To run a server, you need to provide your new node a public key of a wallet so when this node mines a block, network will grant 1 bitcoin to this wallet. To generate a wallet run **wallet_ui.py** and hit 'Generate a new Wallet' button. It will create a text file that contains your public and private keys. You can copy the public key from wallet_ui.py window or open the generated text file and copy the * *public_key* * value. You will use this value when creating a node.
    For first node of the system you just need to provide your public key as an option.
    * `$ pipenv run python node.py -a [YOUR PUBLIC KEY]` 
    For next nodes you need to provide a public key and IP of a running node. Thus, new node will communicate this running node, register itself to this running node and all it's neighbours and new node will register other nodes to itself. Then it will fetch the most up to date chain. To sum up, when you provide a running node IP, new node will be automatically join the system and it will be ready to make transactions and mine. You can also provide a port number to run multiple nodes on the same computer using *-p* keyword.
    * `$ pipenv run python node.py -a [YOUR PUBLIC KEY] -p [PORT NUMBER (eg. 5001)] -n [IP OF A RUNNING NODE(eg. http://localhost:5000)]` 
![run_server](https://www.dropbox.com/s/jzk7xf93ryihx8c/2.png?raw=1 "Run your first node")
    
4. Mine a block by sending a get request to your **node/mine**. I've used Postman to make a request.
![mine_a_block](https://www.dropbox.com/s/n8muglaibul1h9s/3.png?raw=1 "Mine a block")

5. Refresh your balance on the Wallet window to see if network has granted you a coin as a reward of mining a block.
![refresh_balance](https://www.dropbox.com/s/r7l4q7nhktrb9er/4.png?raw=1 "Your first coin")

6. You can open a new **wallet_ui.py** and generate a new wallet and send this new wallet some coins. Your transactions will be added to the chain after a node mined a block. Remember that a client sends transaction request to main node and all it's neighbours so it doesn't matter which node mined a block. Your transaction will be registered if the node who mined the block is in the neighbours list of main node. Since every node register itself to nodes in the system when they started to run, every node will be registered on each other under normal conditions.
![make_transaction](https://www.dropbox.com/s/ioitugwndzs3ccs/5.png?raw=1 "Make a transaction")

7. You can run new servers(nodes) as much as you want to make your system distributed. If you are running servers on the same computer just make sure every node has a unique port number.
* `$ pipenv run python node.py -a [YOUR PUBLIC KEY] -p [PORT NUMBER (eg. 5001)] -n [IP OF A RUNNING NODE(eg. http://localhost:5000)]` 

8. You can also look at the chain by sending a get request to a node.
![get_chain](https://www.dropbox.com/s/3lk254i77koc6ys/6.png?raw=1 "Blockchain Structure")
