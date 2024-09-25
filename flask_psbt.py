from flask import Flask, request, render_template
import subprocess

app = Flask(__name__)

# ======= Route to show form and collect recipient address ======= #
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle PSBT generation
@app.route('/generate_psbt', methods=['POST'])
def generate_psbt():
    # Get recipient address from the form
    recipient_address = request.form.get('recipient_address')

    # Validate recipient address
    if not recipient_address:
        return render_template('index.html', error="Recipient address is required")

    # Call the PSBT display script using subprocess
    try:
        # Using subprocess to call the psbt_display.py script and passing recipient_address as an argument
        subprocess.Popen(['python3', 'psbt.py', recipient_address])
        return render_template('index.html', message="PSBT is being displayed on the e-ink screen!")
    except Exception as e:
        return render_template('index.html', error=f"Failed to display PSBT: {str(e)}")

# This route will receive the signed PSBT via POST
@app.route('/broadcast_psbt', methods=['POST'])
def broadcast_psbt():
    signed_psbt_base64 = request.form.get('signed_psbt')

    if not signed_psbt_base64:
        return jsonify({"error": "No signed PSBT provided"}), 400

    try:
        # Decode and deserialize the signed PSBT
        signed_psbt_bytes = base64.b64decode(signed_psbt_base64)
        signed_psbt = PartiallySignedTransaction.deserialize(signed_psbt_bytes)
        raw_transaction = signed_psbt.tx.serialize().hex()  # Get the final raw transaction

        # Broadcast the transaction using Blockstream API or your preferred Bitcoin node API
        broadcast_url = "https://blockstream.info/api/tx"
        response = requests.post(broadcast_url, data=raw_transaction)

        if response.status_code == 200:
            return jsonify({"message": "Transaction broadcast successfully!"}), 200
        else:
            return jsonify({"error": "Failed to broadcast transaction", "details": response.text}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to decode or broadcast PSBT: {str(e)}"}), 500

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
