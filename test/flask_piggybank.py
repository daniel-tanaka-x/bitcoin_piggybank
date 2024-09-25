from flask import Flask, request, render_template, jsonify
import subprocess
import os
import json
import base64
import requests
from bitcointx.wallet import PartiallySignedTransaction

app = Flask(__name__)

# ======= Route to show form and collect recipient address ======= #
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle PSBT generation
@app.route('/generate_psbt', methods=['POST'])
def generate_psbt():
    recipient_address = request.form.get('recipient_address')

    if not recipient_address:
        return render_template('index.html', error="Recipient address is required")

    try:
        # Call the PSBT script and capture output
        process = subprocess.Popen(['python3', 'generate_psbt.py', recipient_address], stdout=subprocess.PIPE)
        psbt_data, _ = process.communicate()

        # Convert and split PSBT into chunks for QR codes
        psbt_data_str = psbt_data.decode('utf-8')
        chunk_size = 200
        psbt_chunks = [psbt_data_str[i:i + chunk_size] for i in range(0, len(psbt_data_str), chunk_size)]

        return render_template('psbt.html', psbt_chunks=psbt_chunks)

    except Exception as e:
        return render_template('index.html', error=f"Failed to generate PSBT: {str(e)}")


# Route to broadcast signed PSBT
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

# Route to set Wi-Fi credentials and zpub
@app.route('/setup_wifi_and_zpub', methods=['POST'])
def setup_wifi_and_zpub():
    ssid = request.form.get('ssid')
    password = request.form.get('password')
    zpub = request.form.get('zpub')

    if not ssid or not password or not zpub:
        return jsonify({"error": "All fields (SSID, password, and zpub) are required"}), 400

    # Set up Wi-Fi credentials by editing the wpa_supplicant.conf file
    try:
        wpa_supplicant_conf = "/etc/wpa_supplicant/wpa_supplicant.conf"
        with open(wpa_supplicant_conf, "a") as wpa_file:
            wpa_file.write(
                '\nnetwork={{\n'
                '    ssid="{}"\n'
                '    psk="{}"\n'
                '}}\n'.format(ssid, password)
            )
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'])  # Reconfigure Wi-Fi without reboot
    
    except Exception as e:
        return jsonify({"error": f"Failed to set Wi-Fi credentials: {str(e)}"}), 500


    # Set up the zpub in the zpub.json file
    try:
        zpub_data = {"zpub": zpub}
        with open('zpub.json', 'w') as zpub_file:
            json.dump(zpub_data, zpub_file)
    except Exception as e:
        return jsonify({"error": f"Failed to save zpub: {str(e)}"}), 500

    return jsonify({"message": "Wi-Fi credentials and zpub set successfully! Reconnect to the new Wi-Fi."}), 200

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
