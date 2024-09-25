import sys
import base64
import requests
from bitcointx.core.psbt import PartiallySignedTransaction

def broadcast_transaction(signed_psbt_base64):
    try:
        # Decode the signed PSBT from base64
        signed_psbt_bytes = base64.b64decode(signed_psbt_base64)
        signed_psbt = PartiallySignedTransaction.deserialize(signed_psbt_bytes)
        raw_transaction = signed_psbt.tx.serialize().hex()

        # Broadcast the transaction using Blockstream API (or your node API)
        broadcast_url = "https://blockstream.info/api/tx"
        response = requests.post(broadcast_url, data=raw_transaction)

        if response.status_code == 200:
            print("Transaction broadcast successfully!")
            return True
        else:
            print(f"Failed to broadcast transaction: {response.text}")
            return False
    except Exception as e:
        print(f"Error during broadcasting: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python broadcast.py <signed_psbt_base64>")
        sys.exit(1)

    signed_psbt_base64 = sys.argv[1]
    broadcast_transaction(signed_psbt_base64)
