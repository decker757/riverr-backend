from xrpl_utilities import *

# INJECTING CURRENCY
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
from xrpl.models.transactions import AccountSet
from xrpl.transaction import autofill_and_sign, submit_and_wait

# tx = AccountSet(
#     account=wallet3.classic_address,
#     set_flag=8  # ASF_DEFAULT_RIPPLE
# )

# signed = autofill_and_sign(tx, client, wallet3)
# response = submit_and_wait(signed, client)
# print(response.result)

TrustLine.create_trustline(
    wallet=wallet1,
    issuer_address=wallet3.classic_address,
    currency_code="RLUSD",
    limit=10000000,
    client=client
)

# TrustLine.send_issued_currency(
#     wallet=wallet1,
#     destination=wallet2.classic_address,
#     currency_code="ETH",
#     issuer=wallet3.classic_address,
#     amount=100.0,
#     client=client
# )
# TrustLine.clear_no_ripple_flag(
#     wallet=wallet3,  # issuer
#     issuer_address=wallet1.classic_address,
#     currency_code="ETH",
#     limit=1000000,
#     client=client
# )

# TrustLine.clear_no_ripple_flag(
#     wallet=wallet3,
#     issuer_address=wallet2.classic_address,
#     currency_code="ETH",
#     limit=1000000,
#     client=client
# )

# lines = AccountLines(account=wallet1.classic_address, peer=wallet3.classic_address)
# print(client.request(lines).result)

