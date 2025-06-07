from xrpl.clients import JsonRpcClient
from xrpl.models import EscrowCreate, EscrowFinish
from xrpl.transaction import submit_and_wait, XRPLReliableSubmissionException
from xrpl.wallet import generate_faucet_wallet, Wallet
from xrpl.utils import datetime_to_ripple_time
from cryptoconditions import PreimageSha256
from datetime import datetime
import os

class XRPLClient:
    def __generate_condition(self):
        randy = os.urandom(32)
        fullfillment = PreimageSha256(preimage=randy)
        return (fullfillment.condition_binary.hex().upper(), fullfillment.serialize_binary().hex().upper())

    def __init__ (self, url):
        self.client = JsonRpcClient(url)
    
    def create_escrow_tx(self, sender: str, receiver: str, amount: int, cancel_after: int):
        # returns (tx, condition, fullfillment_serialized)
        
        """
        Create an EscrowCreate transaction.
        
        :param sender: The address of the sender (account creating the escrow).
        :param receiver: The address of the receiver (account receiving the escrow).
        :param amount: The amount in drops to be held in escrow (1 XRP = 1,000,000 drops).
        :param cancel_after: The time after which the escrow can be canceled.
        :return: Transaction, Condition (in  hexadecimal format) and Fulfillment secrialized (in hexadecimal format) of the escrow transaction.
        """

        condition, fullfillment = self.__generate_condition()


        tx = EscrowCreate(
            account=sender,
            amount=str(amount),  # Amount in drops
            destination=receiver,
            cancel_after=datetime_to_ripple_time(datetime.now()) + cancel_after,
            condition=condition,  # Condition can be set later
        )

        return (tx, condition, fullfillment)
    
    def finish_escrow_tx(self, account: str, owner: str, offer_sequence: int, condition: str, fullfillment: str):
        """
        Create an EscrowFinish transaction.
        
        :param account: The address of the account finishing the escrow (usually the receiver).
        :param owner: The address of the escrow owner (account finishing the escrow).
        :param offer_sequence: The sequence number of the EscrowCreate transaction.
        :param condition: The condition of the escrow in hexadecimal format.
        :param fullfillment: The serialized fulfillment in hexadecimal format.
        :return: An EscrowFinish transaction object.
        """

        return EscrowFinish(
            account=account,
            owner=owner,
            offer_sequence=offer_sequence,
            condition=condition,
            fulfillment=fullfillment
        )



