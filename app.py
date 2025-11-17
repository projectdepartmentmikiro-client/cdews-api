import os
from flask import Flask, request, jsonify
from google.cloud import storage

# ----------------------------
# Configuration
# ----------------------------
BUCKET_NAME = os.environ.get("BUCKET_NAME")
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")

# Path to Render secret file (service account JSON)
SERVICE_ACCOUNT_FILE = "/opt/render/project/secrets/service-account.json"

# ----------------------------
# Initialize Google Cloud Storage
# ----------------------------
try:
    client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
    bucket = client.bucket(BUCKET_NAME)
except Exception as e:
    print(f"[ERROR] Failed to initialize GCS client: {e}")
    raise

# ----------------------------
# Initialize Flask
# ----------------------------
app = Flask(__name__)

# ----------------------------
# Helper function: signed URL
# ----------------------------
def get_signed_url(blob_name, expiration=3600):
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(version="v4", expiration=expiration, method="GET")

# ----------------------------
# Routes
# ----------------------------
@app.route("/get-image", methods=["GET"])
def get_image():
    key = request.headers.get("x-api-key")
    secret = request.headers.get("x-api-secret")

    # Validate API key and secret
    if key != API_KEY or secret != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    try:
        blob = bucket.blob(f"annotated/{filename}")

        if not blob.exists():
            return jsonify({"error": "File not found"}), 404

        url = get_signed_url(f"annotated/{filename}")
        return jsonify({"image_url": url})

    except Exception as e:
        # Debug output for Render logs
        print(f"[ERROR] Exception in /get-image: {e}")
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Run Flask
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[INFO] Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)
