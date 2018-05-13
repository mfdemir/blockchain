import hashlib
import json
from time import time
from urllib.parse import urlparse
import sys
import ecdsa
import base64
import requests
from flask import Flask, jsonify, request
import os.path

# For asking other nodes to resolve
from threading import Thread

network_sender_name = 'network'


class Blockchain:
    '''
    This is the main class, it contains all methods and variables.
    '''
    def __init__(self, neighbour_url=None):
        '''
        Node will try to update itself to the most up to date chain and it will try to notify other nodes in the
        system.
        :param neighbour_url: When instantiating a node, if you provide an another node's url, this node will be
        automatically introduce itself to the neighbours of the provided node and it will automatically get the
        most up to date chain via communicating other nodes. If no url provided, this node will see itself as the
        first node of a blockchain.
        '''
        # A list of transactions which will be added to the block if this node mines the next block
        self.current_transactions = []
        # Blockchain itself
        self.chain = []
        # Other nodes in the system will be stored here to communicate later
        self.nodes = set()
        # Url of this node
        self.url = 'http://{}:{}'.format(host, port)

        # If there is no neighbour node url provided, this node will try to load its blockchain from file,
        # and if it can not find a file that contains a blockchain, it will generate the genesis block and,
        # consider itself as the first node in its blockchain system.
        if neighbour_url is None:
            # If there is not a known neighbour, try to load chain from file
            self.chain = self.load_chain_from_file()
            # If there is no chain file found, start a new chain from genesis block
            if self.chain == []:
                # Create the genesis block
                self.new_block(previous_hash='1', proof=100)
        else:  # If there is a known neighbour, add it to nodes list and add yourself to it's nodes list.
            parsed_url = urlparse(neighbour_url)  # Check if url is valid
            if parsed_url.netloc:
                r = requests.get('{}/nodes/get'.format(neighbour_url))
                if r.status_code == 200:
                    print('*****', r.json())
                    response_json = r.json()  # Get neighbours of neighbour
                    if 'nodes' in response_json:
                        for node in response_json['nodes']:
                            if node != self.url and not node in self.nodes:
                                self.register_node(node)
                                r = requests.post('{}/nodes/register'.format(node), json={'nodes': [self.url]})
                                print('Node {} added to list and registered and response code is {}'.format(node,
                                                                                                            r.status_code))
                else:
                    print('Neighbour is not valid. Response code is ', r.status_code)
            else:
                print('Neighbour URL is not in a valid format')

            self.register_node(neighbour_url)
            r = requests.post('{}/nodes/register'.format(neighbour_url), json={'nodes': [self.url]})
            print('Node {} added to list and registered and response code is {}'.format(neighbour_url, r.status_code))

            # Get the most up to date chain from other nodes
            self.resolve_conflicts()


    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            # self.nodes.add(parsed_url.netloc)
            self.nodes.add(parsed_url.geturl())
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            # self.nodes.add(parsed_url.path)
            self.nodes.add(parsed_url.geturl())
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1
        balances = {}  # Keep balances of wallets who made transactions to check if they are valid
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            # Get balances to check later
            for transaction in block['transactions']:
                sender = transaction['sender']
                recipient = transaction['recipient']
                amount = transaction['amount']
                if sender in balances:
                    balances[sender] -= amount
                else:
                    if sender != network_sender_name:
                        # A person who has never received a coin can not send one. Seems like there is a problem.
                        return False
                    elif amount != 1:  # If sender is network, amount should be equal to 1
                        return False

                if recipient in balances:
                    balances[recipient] += amount
                else:
                    balances[recipient] = amount

            last_block = block
            current_index += 1

        # If there is a negative balance, it means this chain is not valid
        if not all(balances[k] >= 0 for k in balances):
            return False

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest valid one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.set_chain(new_chain)
            #self.chain = new_chain
            self.current_transactions = []
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain_add_block(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.

        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def get_balance(self, sender):
        """
        Calculates the balance of a wallet by looking all blocks in the chain

        :param sender: <str> Public key of the wallet
        :return: Balance of wallet
        """

        balance = 0

        for transaction in self.current_transactions:
            if transaction['sender'] == sender:
                balance -= transaction['amount']
            elif transaction['recipient'] == sender:
                balance += transaction['amount']

        for block in blockchain.chain:
            for transaction in block['transactions']:
                if transaction['sender'] == sender:
                    balance -= transaction['amount']
                elif transaction['recipient'] == sender:
                    balance += transaction['amount']
        return balance

    @staticmethod
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

    def save_chain_to_file(self):
        filename = f'chain_of_{port}.blockchain'
        with open(filename, 'w') as f:
            json.dump(self.chain, f)
        print('Chain saved.')

    def load_chain_from_file(self):
        filename = f'chain_of_{port}.blockchain'
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                print('Chain loaded.')
                return json.loads(f.read())
        else:
            return []

    def set_chain(self, new_chain):
        self.chain = new_chain
        self.save_chain_to_file()

    def chain_add_block(self,block):
        self.chain.append(block)
        self.save_chain_to_file()

    @staticmethod
    def send_req_and_print_status(url):
        """
        This method is used to send all other nodes that "I've mined a block"

        :param url: url of the node to send request
        """
        r = requests.get(url)
        print('{} responded {}'.format(url, r.status_code))


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
# node_identifier = str(uuid4()).replace('-', '')
node_identifier = None

# Instantiate the blockchain
blockchain = None


@app.route('/mine', methods=['GET'])
def mine():
    """
    Mines a block and tells other nodes about this.
    """
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is network to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender=network_sender_name,
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    # Tell other nodes that you have mined a block. This operation is done asynchronously because
    # we don't want to wait other nodes to verify our operation.
    for node in blockchain.nodes:
        Thread(target=blockchain.send_req_and_print_status(), args=['{}/nodes/resolve'.format(node)]).start()

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'signature', 'message']
    if not all(k in values for k in required):
        response = {'message': f'Missing components'}
        return jsonify(response), 400

    # Check Signature Validity
    if not blockchain.validate_signature(values['sender'], values['signature'], values['message']):
        response = {'message': f'Signature validation failed.'}
        return jsonify(response), 400

    # Check amount is > 0
    amount = values['amount']
    if values['amount'] <= 0:
        response = {'message': f'Transaction amount should be bigger than 0, amount = {amount}'}
        return jsonify(response), 400

    # Check Transaction Validity
    if blockchain.get_balance(values['sender']) - values['amount'] < 0:
        response = {'message': f'Your balance is not enough to make this transaction, amount = {amount}'}
        return jsonify(response), 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/transactions/get_balance', methods=['POST'])
def get_balance():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['public_key']
    if not all(k in values for k in required):
        return 'Missing values', 400

    balance = blockchain.get_balance(values['public_key'])
    response = {'balance': balance}
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """
    Register a list of nodes
    """
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    response = {
        'nodes': list(blockchain.nodes),
        'length': len(blockchain.nodes),
    }
    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':

    # USAGE:
    # Make sure Python 3.6+ is installed.
    # Install pipenv.
    # $ pip install pipenv
    # Create a virtual environment and specify python.exe location
    # $ pipenv --python=C:\Users\[USERNAME]\AppData\Local\Programs\Python\Python36-32\python.exe
    # Install requirements.
    # $ pipenv install
    # Run the server:
    #     Note: You need to generate a wallet for every node in order to run a server
    #     For first node:
    #     $ pipenv run python blockchain.py -a [Public key of the wallet you have generated using wallet_ui.py]
    #     For other nodes:
    #     $ pipenv run python blockchain.py -p [a Port number eg. 5001] -n [Url of a working node eg. http://localhost:5000] -a [Public key of the wallet you have generated using wallet_ui.py]

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-n', '--neighbour', default=None, type=str, help='Neighbour to get the chain from')
    parser.add_argument('-a', '--address', default=None, type=str, help='Public address of miner')
    args = parser.parse_args()
    port = args.port
    host = 'localhost'
    node_identifier = args.address
    if node_identifier is None:
        print('Miner address should be entered. Usage:\nblockchain.py -a your-public-key')
        sys.exit(-1)
    blockchain = Blockchain(args.neighbour)

    app.run(host=host, port=port, debug=True)
