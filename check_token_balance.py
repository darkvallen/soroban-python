"""This example demonstrates how to invoke an auth contract with [Transaction Invoker] authrization.

See https://soroban.stellar.org/docs/how-to-guides/auth
See https://soroban.stellar.org/docs/learn/authorization#transaction-invoker
"""
import time

from stellar_sdk import (
    Network,
    Keypair,
    TransactionBuilder,
)
from stellar_sdk import xdr as stellar_xdr
from stellar_sdk.soroban import SorobanServer, ContractAuth, AuthorizedInvocation
from stellar_sdk.soroban.soroban_rpc import TransactionStatus
from stellar_sdk.soroban.types import Address

rpc_server_url = "https://horizon-futurenet.stellar.cash:443/soroban/rpc"
soroban_server = SorobanServer(rpc_server_url)
network_passphrase = Network.FUTURENET_NETWORK_PASSPHRASE

contract_id = "d93f5c7bb0ebc4a9c8f727c5cebc4e41194d38257e1d0d910356b43bfc528813"
tx_submitter_kp = Keypair.from_secret(
    "SCHKLGAGY7QGWUKUFDGHEQMSCPFZNMLEHQE6Y6WPGYGHQIM23T3NJE3C"
)

func_name = "balance"
args = [Address(tx_submitter_kp.public_key)]

invocation = AuthorizedInvocation(
    contract_id=contract_id,
    function_name=func_name,
    args=args,
    sub_invocations=[],
)

contract_auth = ContractAuth(
    address=None,
    nonce=None,
    root_invocation=invocation,
)

source = soroban_server.load_account(tx_submitter_kp.public_key)
tx = (
    TransactionBuilder(source, network_passphrase)
    .add_time_bounds(0, 0)
    .append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name=func_name,
        parameters=args,
        auth=[contract_auth],
    )
    .build()
)

simulate_transaction_data = soroban_server.simulate_transaction(tx)
print(f"simulated transaction: {simulate_transaction_data}")

print(f"setting footprint and signing transaction...")
assert simulate_transaction_data.results is not None
tx.set_footpoint(simulate_transaction_data.results[0].footprint)
tx.sign(tx_submitter_kp)

print(f"Signed XDR:\n{tx.to_xdr()}")

send_transaction_data = soroban_server.send_transaction(tx)
print(f"sent transaction: {send_transaction_data}")

while True:
    print("waiting for transaction to be confirmed...")
    get_transaction_status_data = soroban_server.get_transaction_status(
        send_transaction_data.id
    )
    if get_transaction_status_data.status != TransactionStatus.PENDING:
        break
    time.sleep(3)
print(f"transaction status: {get_transaction_status_data}")

if get_transaction_status_data.status == TransactionStatus.SUCCESS:
    result = stellar_xdr.SCVal.from_xdr(get_transaction_status_data.results[0].xdr)  # type: ignore
    result_str = str(result)
    value = int(result_str.split("<Uint64 [uint64=")[1].split("]>")[0])


    print(f"Your Token Balance: {value}")