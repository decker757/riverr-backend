from xrpl.clients import JsonRpcClient
from xrpl.models.requests.account_info import AccountInfo
from xrpl.models.transactions import TrustSet, TrustSetFlag, Payment, AccountSet, AccountSetFlag
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill_and_sign, submit_and_wait
from xrpl.models.requests import AccountLines, AccountTx
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl import XRPLException

import json
import xrpl

from dotenv import load_dotenv

import os 

load_dotenv()

wallet1 = Wallet.from_seed(os.getenv("WALLET1_SEED"))
wallet2 = Wallet.from_seed(os.getenv("WALLET2_SEED"))
wallet3 = Wallet.from_seed(os.getenv("WALLET3_SEED"))
wallet4 = Wallet.from_seed(os.getenv("WALLET4_SEED"))
wallet5 = Wallet.from_seed(os.getenv("WALLET5_SEED"))
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

#Account Info
def get_account_info(address):
    acc_info = AccountInfo(
        account=address,
        ledger_index="validated",
        strict=True,
    )
    response = client.request(acc_info)
    account_data = response.result["account_data"]
    
    return account_data

#Get Account Balance in XRP
def get_balance(address):
    return float(get_account_info(address)["Balance"])/1000000

def create_dummy_accounts():
    wallet = generate_faucet_wallet(client, debug=True)
    print("Classic address:", wallet.classic_address)
    print("Seed:", wallet.seed)

#Injecting foreign currencies into test accounts
def inject_issued_currency(issuer_wallet: Wallet, recipient_address: str, currency: str, value: float, client: JsonRpcClient):
    """
    Issues custom currency (IOU) from issuer to recipient wallet.

    Args:
        issuer_wallet (Wallet): XRPL wallet of the issuer.
        recipient_address (str): Classic address of the recipient wallet.
        currency (str): Currency code (e.g., 'BTC', 'USD').
        value (float): Amount of IOU to issue.
        client (JsonRpcClient): Connected XRPL client.

    Returns:
        dict: Result of the transaction submission.
    """
    payment_tx = Payment(
        account=issuer_wallet.classic_address,
        destination=recipient_address,
        amount=IssuedCurrencyAmount(
            currency=currency,
            issuer=issuer_wallet.classic_address,
            value=str(value)
        )
    )

    signed_tx = autofill_and_sign(payment_tx, client, issuer_wallet)
    response = submit_and_wait(signed_tx, client)
    return response.result

issuer_wallet = Wallet.from_seed(seed=os.getenv("WALLET3_SEED"))
recipient = os.getenv("WALLET1_ADDRESS")
# inject_issued_currency(
#     issuer_wallet=issuer_wallet,
#     recipient_address=recipient,
#     currency="ETH",
#     value=500,
#     client=client
# )

# inject_issued_currency(
#     issuer_wallet=wallet3,
#     recipient_address=wallet2.classic_address,
#     currency="ETH",
#     value=1000,
#     client=client
# )


class Transaction:
    @staticmethod
    def prepare_transaction(value, from_account, to_account):
        return xrpl.models.transactions.Payment(
            account=from_account,
            amount=xrpl.utils.xrp_to_drops(value),
            destination=to_account,
        )

    @staticmethod
    def sign_transaction(payment, wallet, client):
        signed_tx = xrpl.transaction.autofill_and_sign(payment, client, wallet)
        max_ledger = signed_tx.last_ledger_sequence
        tx_id = signed_tx.get_hash()
        return signed_tx, max_ledger, tx_id

    @staticmethod
    def submit_transaction(signed_tx, client):
        try:
            tx_response = xrpl.transaction.submit_and_wait(signed_tx, client)
            return tx_response
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            raise Exception(f"Submit failed: {e}")

    @staticmethod
    def get_balance(address, client):
        acc_info = AccountInfo(
            account=address,
            ledger_index="validated",
            strict=True,
        )
        response = client.request(acc_info)
        new_balance_drops = response.result["account_data"]["Balance"]
        return float(new_balance_drops) / 1_000_000

    @staticmethod
    def print_transaction_results(tx_response, tx_id):
        print(json.dumps(tx_response.result, indent=4, sort_keys=True))
        print(f"Explorer link: https://testnet.xrpl.org/transactions/{tx_id}")
        metadata = tx_response.result.get("meta", {})
        if metadata.get("TransactionResult"):
            print("Result code:", metadata["TransactionResult"])
        if metadata.get("delivered_amount"):
            print("XRP delivered:", xrpl.utils.drops_to_xrp(
                metadata["delivered_amount"]))

    @staticmethod
    def execute(value, from_account, from_wallet, to_account, client):
        payment = Transaction.prepare_transaction(value, from_account, to_account)
        signed_tx, max_ledger, tx_id = Transaction.sign_transaction(payment, from_wallet, client)
        tx_response = Transaction.submit_transaction(signed_tx, client)
        Transaction.print_transaction_results(tx_response, tx_id)
        return Transaction.get_balance(from_account, client)
    
    @staticmethod
    def get_transaction_history(address, limit = 10):
        tx_request = AccountTx(
            account=address,
            ledger_index_min=-1,
            ledger_index_max=-1,
            limit=limit,
            binary=False,
            forward=False,
        )
        response = client.request(tx_request)
        return response.result.get("transactions", [])


class TrustLine:
    @staticmethod
    def create_trustline(wallet, issuer_address, currency_code, limit, client):
        """
        Establishes a trustline between the wallet and the issuer for a specific currency.

        Args:
            wallet (xrpl.wallet.Wallet): The user's XRPL wallet.
            issuer_address (str): The address of the token issuer.
            currency_code (str): Currency code (e.g. "USD").
            limit (float): The trust limit amount.
            client (xrpl.clients.JsonRpcClient): The XRPL client object.

        Returns:
            dict: XRPL response from transaction submission.
        """

        trust_set_tx = TrustSet(
            account=wallet.classic_address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer_address,
                value=str(limit)
            )
        )
        signed_tx = autofill_and_sign(trust_set_tx, client, wallet)  
        response = submit_and_wait(signed_tx, client)
        return response.result
    
    @staticmethod
    def delete_trustline(wallet, issuer_address, currency_code, client):
        """
        Deletes a trust line by setting its limit to 0.

        Args:
            wallet (xrpl.wallet.Wallet): The user's XRPL wallet.
            issuer_address (str): The issuer of the token.
            currency_code (str): The currency code of the trustline.
            client (xrpl.clients.JsonRpcClient): XRPL client.

        Returns:
            dict: XRPL response.
        """
        trust_delete_tx = TrustSet(
            account=wallet.classic_address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer_address,
                value="0"  # Setting limit to 0 removes trustline
            )
        )
        signed_tx = autofill_and_sign(trust_delete_tx, client, wallet)
        response = submit_and_wait(signed_tx, client)
        return response.result
    
    @staticmethod
    def send_issued_currency(wallet: Wallet, destination: str, currency_code: str, 
                            issuer: str, amount: float, client) -> dict:
        """
        Safely sends an IOU payment through the issuer.
        
        Args:
            wallet: Sender's wallet (must hold the IOU)
            destination: Receiver's address (must trust issuer)
            currency_code: Currency to send (e.g., "ETH")
            issuer: Original issuer's address (Wallet 3 in your case)
            amount: Amount to send (will auto-convert to string)
            client: XRPL client connection
            
        Returns:
            Transaction result dictionary
            
        Raises:
            XRPLException: If any pre-check fails or transaction errors occur
        """
        # ===== 1. Pre-flight Checks =====
        # Check receiver's trust line
        receiver_lines = AccountLines(account=destination, peer=issuer)
        receiver_response = client.request(receiver_lines)
        
        if not receiver_response.result.get("lines"):
            raise XRPLException(f"Receiver {destination} doesn't trust issuer {issuer} for {currency_code}")

        # Check sender's balance
        sender_lines = AccountLines(account=wallet.classic_address, peer=issuer)
        sender_response = client.request(sender_lines)
        
        sender_balance = next(
            (float(line["balance"]) 
             for line in sender_response.result["lines"] 
             if line["currency"] == currency_code),
            0
        )
        
        if sender_balance < float(amount):
            raise XRPLException(
                f"Insufficient balance. Sender has {sender_balance} {currency_code}, "
                f"tried to send {amount}"
            )

        # ===== 2. Prepare Transaction =====
        payment = Payment(
            account=wallet.classic_address,
            destination=destination,
            amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer,
                value=str(amount)
            ),
            send_max=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer,
                value=str(amount)
            )
        )

        # ===== 3. Submit Transaction =====
        try:
            signed = autofill_and_sign(payment, client, wallet)
            response = submit_and_wait(signed, client)
            
            if response.is_successful():
                return response.result
            else:
                raise XRPLException(f"Transaction failed: {response.result}")
                
        except Exception as e:
            raise XRPLException(f"Submission error: {str(e)}")


    @staticmethod
    def clear_no_ripple_flag(wallet, issuer_address, currency_code, limit, client):
        """
        Disables the No Ripple flag on a trust line.

        Args:
            wallet (Wallet): The wallet to set the trust line for.
            issuer_address (str): The address of the token issuer.
            currency_code (str): The currency (e.g., "ETH").
            limit (float): The trust limit (e.g., 1000000).
            client (JsonRpcClient): XRPL client.

        Returns:
            dict: XRPL transaction result.
        """
        trust_set_tx = TrustSet(
            account=wallet.classic_address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=issuer_address,
                value=str(limit)
            ),
            flags=TrustSetFlag.TF_CLEAR_NO_RIPPLE
        )

        signed_tx = autofill_and_sign(trust_set_tx, client, wallet)
        response = submit_and_wait(signed_tx, client)
        return response.result
    
class TrustLineAnalytics:
    @staticmethod
    def decode_currency(currency_hex):
        try:
            decoded = bytes.fromhex(currency_hex).decode("ascii").rstrip('\x00')
            return decoded
        except Exception:
            return currency_hex  # fallback to raw if invalid ASCII
        
    @staticmethod
    def get_trustlines(address):
        result = client.request(AccountLines(account=address)).result
        return result.get("lines", [])
    
    @staticmethod
    def summarize_trustlines(address):
        lines = TrustLineAnalytics.get_trustlines(address)
        summary = {
            "total_trustlines": 0,
            "currencies": {},
        }

        for line in lines:
            currency = TrustLineAnalytics.decode_currency(line["currency"])
            issuer = line["account"]
            balance = float(line["balance"])
            limit = float(line["limit"])

            if (
                float(line["balance"]) == 0 and
                float(line["limit"]) == 0 and
                float(line.get("limit_peer", 0)) == 0
            ):
                continue

            summary["total_trustlines"] += 1

            if currency not in summary["currencies"]:
                summary["currencies"][currency] = []

            summary["currencies"][currency].append({
                "issuer": issuer,
                "balance": balance,
                "limit": limit,
            })

        currency_summary = {}
        for currency, entries in summary["currencies"].items():
            total_balance = sum(e["balance"] for e in entries)
            total_limit = sum(e["limit"] for e in entries)
            currency_summary[currency + "_summary"] = {
                "total_balance": total_balance,
                "total_limit": total_limit
            }

        summary["currencies"].update(currency_summary)  # safe to do after iteration

        return summary
    


# try:
#     result = TrustLine.send_issued_currency(
#         wallet=wallet1,  # 👈 must already hold ETH issued by wallet3
#         destination=wallet2.classic_address,  # 👈 must trust wallet3
#         currency_code="ETH",
#         issuer=wallet3.classic_address,
#         amount=10,
#         client=client
#     )
#     print("✅ Success:", result)
# except XRPLException as e:
#     print("❌ Failed:", str(e))

