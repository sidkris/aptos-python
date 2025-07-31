import asyncio
from aptos_sdk.account import Account
from aptos_sdk.async_client import FaucetClient, RestClient
from aptos_sdk.transactions import EntryFunction, TransactionPayload, TransactionArgument, RawTransaction
from aptos_sdk.bcs import Serializer
import time
import logging 

logging.basicConfig(level = logging.INFO, format = "%(levelname)s, %(asctime)s, %(message)s")

# Network configuration
NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
FAUCET_URL = "https://faucet.devnet.aptoslabs.com"


async def main():
    rest_client = RestClient(NODE_URL)
    faucet_client = FaucetClient(FAUCET_URL, rest_client)

    logging.info("Connected to Aptos Devnet.")

    alice = Account.generate()
    bob = Account.generate()

    logging.info("=== Addresses ===")
    logging.info(f"Alice's address: {alice.address()}")
    logging.info(f"Bob's address: {bob.address()}")

    logging.info("\n=== Funding accounts ===")
    alice_amount = 100_000_000  # 1 APT = 100,000,000 octas
    bob_amount = 0  # Bob starts with 0 APT

    await faucet_client.fund_account(alice.address(), alice_amount)
    logging.info("Account funded successfully")


    # Check initial balances
    alice_balance = await rest_client.account_balance(alice.address())
    bob_balance = await rest_client.account_balance(bob.address())

    logging.info("\n=== Initial Balances ===")
    logging.info(f"Alice: {alice_balance} octas")
    logging.info(f"Bob: {bob_balance} octas")


    logging.info("\n\n*** 1. Building the Transaction ***\n")

    entry_function = EntryFunction.natural(
            "0x1::aptos_account",  # Module address and name
            "transfer",            # Function name
            [],                    # Type arguments (empty for this function)
            [
                # Function arguments with their serialization type
                TransactionArgument(bob.address(), Serializer.struct),  # Recipient address
                TransactionArgument(1000, Serializer.u64),              # Amount to transfer (1000 octas)
            ],
        )   

    # get the chain id for the transaction
    chain_id = await rest_client.chain_id()

    # get the sender's current sequence number
    account_data = await rest_client.account(alice.address())
    sequence_number = int(account_data["sequence_number"])

    # create the raw transaction with all the required fields
    raw_transaction = RawTransaction(
        sender = alice.address(),                                   # Sender's address
        sequence_number = sequence_number,                          # Sequence number to prevent a relay attack
        payload = TransactionPayload(entry_function),               
        max_gas_amount = 2000,                                      # Max gas units to use
        gas_unit_price = 100,                                       # Price per gas unit in octas
        expiration_timestamps_secs = int(time.time()) + 600,        # Expires in 10 mins
        chain_id = chain_id,                                        # Chain id to ensure correct network
    )


    logging.info("Transaction built successfully")
    logging.info(f"Sender: {raw_transaction.sender}")                                                   
    logging.info(f"Sequence Number: {raw_transaction.sequence_number}")               
    logging.info(f"Max Gas Amount: {raw_transaction.max_gas_amount}")                  
    logging.info(f"Gas Unit Price: {raw_transaction.gas_unit_price}")
    logging.info(f"Expiration Timestamp: {time.ctime(raw_transaction.expiration_timestamps_secs)}")


    logging.info("\n\n*** 2. Simulating the Transaction ***\n") # Before submitting a transaction, it’s wise to simulate it first to estimate the gas cost. This is like checking shipping costs before sending a package.

    # Create a BCS transaction for simulation
    # This doesn't actually submit the transaction to the blockchain

    simulation_transaction = await rest_client.create_bcs_transaction(alice, TransactionPayload(entry_function))
    simulation_result = await rest_client.simulate_transaction(simulation_transaction, alice) # Simulate tranasaction to estimate gas cost and check for errors

    gas_used = int(simulation_result[0]["gas_used"])
    gas_unit_price = int(simulation_result[0]["gas_unit_price"])
    success = simulation_result[0]["success"]

    logging.info(f"Estimated gas units: {gas_used}")
    logging.info(f"Estimated gas cost: {gas_used * gas_unit_price} octas")
    logging.info(f"Transaction would {'succeed' if success else 'fail'}")


    logging.info("\n\n*** 3. Signing the Transaction ***\n")

    signed_transaction = await rest_client.create_bcs_signed_transaction(
        alice,                                                          # Account with the private key
        TransactionPayload(entry_function),                             # The payload from our transaction
        sequence_number = sequence_number,                              # Using the same sequence number as before
    )


    logging.info("Transaction signed successfully.")


    logging.info("\n\n*** 4. Submitting the Transaction ***\n")
    transaction_hash = await rest_client.submit_bcs_transaction(signed_transaction)
    logging.info(f"Transaction submitted with the hash : {transaction_hash}")


    logging.info("\n\n*** 5. Waiting for Transaction Completion ***\n")
    await rest_client.wait_for_transaction(transaction_hash)

    transaction_details = await rest_client.transaction_by_hash(transaction_hash)
    success = transaction_details["success"]
    vm_status = transaction_details["vm_status"]
    gas_used = transaction_details["gas_used"]

    logging.info(f"Transaction completed with status : {'SUCCESS' if success else 'FAILURE'}")
    logging.info(f"VM Status : {vm_status}")
    logging.info(f"Gas used : {gas_used}")


    alice_final_balance = await rest_client.account_balance(alice.address())
    bob_final_balance = await rest_client.account_balance(bob.address())

    logging.info("\n\n*** Final Balances ***\n")
    logging.info(f"Alice: {alice_final_balance} octas (spent {alice_balance - alice_final_balance} octas on transfer and gas)")
    logging.info(f"Bob: {bob_final_balance} octas (received 1000 octas)")


if __name__ == "__main__":
    asyncio.run(main())