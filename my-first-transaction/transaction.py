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


if __name__ == "__main__":
    asyncio.run(main())