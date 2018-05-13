"""This is going to be your wallet. Here you can do several things:
- Generate a new address (public and private key). You are going
to use this address (public key) to send or receive any transactions. You can
have as many addresses as you wish, but keep in mind that if you
lose its credential data, you will not be able to retrieve it.

- Generate a new wallet
- Send coins to another address
- Get your balance

"""

import requests
import time
import base64
import ecdsa

# In real bitcoin node IP adressess are fetched using DNS seeds or IP adresses believed to point to stable nodes
# are hard-coded into clients. Since we don't have a DNS seed, we need to presume this node is always on.
main_node = 'http://localhost:5000'  # A node url to communicate


def send_transaction(sender_public_key, sender_private_key, recipient_public_key, amount):
    """Sends your transaction to different nodes. Once any of the nodes manage
    to mine a block, your transaction will be added to the blockchain. Despite
    that, there is a low chance your transaction gets canceled due to other nodes
    having a longer chain. So make sure your transaction is deep into the chain
    before claiming it as approved!
    """

    if len(sender_private_key) == 64:
        signature, message = sign_ECDSA_msg(sender_private_key)
        url = '{}/transactions/new'.format(main_node)
        payload = {"sender": sender_public_key,
                   "recipient": recipient_public_key,
                   "amount": amount,
                   "signature": signature.decode(),
                   "message": message}
        headers = {"Content-Type": "application/json"}

        # Get as much as node url's to send transaction request:
        nodes = [main_node]  # Add main node to nodes list
        r = requests.get('{}/nodes/get'.format(main_node))  # Ask main node to give you it's neighbours
        if r.status_code == 200:
            nodes.extend(r.json()['nodes'])  # Add main node's neighbours to nodes list

        results = []
        for node in nodes:
            res = requests.post(f'{node}/transactions/new', json=payload, headers=headers)
            results.append(res.json())
        return results

    else:
        print("Wrong address or key length! Verify and try again.")


def get_balance(public_key=None):
    """Ask a node to calculate your balance. With this you can check your
    wallets balance.
    """
    if public_key is None:
        return 'Error: Public Key is Empty'
    # public_key = input("From: introduce your wallet address (public key)\n")
    payload = {'public_key': public_key}
    res = requests.post('{}/transactions/get_balance'.format(main_node), json=payload)
    if 'balance' in res.json():
        return res.json()['balance']
    else:
        return f'Error: {res.status_code}'


def generate_ECDSA_keys(filename=None):
    """This function takes care of creating your private and public (your address) keys.
    It's very important you don't lose any of them or those wallets will be lost
    forever. If someone else get access to your private key, you risk losing your coins.

    private_key: str
    public_ley: base64 (to make it shorter)
    """
    if filename is None:
        return None, None

    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)  # this is your sign (private key)
    private_key = sk.to_string().hex()  # convert your private key to hex
    vk = sk.get_verifying_key()  # this is your verification key (public key)
    public_key = vk.to_string().hex()
    # we are going to encode the public key to make it shorter
    public_key = base64.b64encode(bytes.fromhex(public_key))

    with open(filename, "w") as f:
        f.write("private_key:{0}\npublic_key:{1}".format(private_key, public_key.decode()))
    print("Your new address and private key are now in the file {0}".format(filename))

    return private_key, public_key


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
