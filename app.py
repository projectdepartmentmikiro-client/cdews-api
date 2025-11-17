import os
from flask import Flask, request, jsonify
from google.cloud import storage

BUCKET_NAME = os.environ.get("BUCKET_NAME")
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
SERVICE_ACCOUNT_FILE = "/opt/render/project/secrets/service-account.json"

try:
    client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
    bucket = client.bucket(BUCKET_NAME)
    print("[INFO] GCS client initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize GCS client: {e}")
    raise

app = Flask(__name__)

def get_signed_url(blob_name, expiration=3600):
    try:
        blob = bucket.blob(blob_name)
        url = blob.generate_signed_url(version="v4", expiration=expiration, method="GET")
        print(f"[INFO] Generated signed URL for {blob_name}")
        return url
    except Exception as e:
        print(f"[ERROR] Failed to generate signed URL for {blob_name}: {e}")
        raise

@app.route("/get-image", methods=["GET"])
def get_image():
    key = request.headers.get("x-api-key")
    secret = request.headers.get("x-api-secret")

    if key != API_KEY or secret != API_SECRET:
        print(f"[WARN] Unauthorized access attempt: key={key}, secret={secret}")
        return jsonify({"error": "Unauthorized"}), 401

    filename = request.args.get("filename")
    if not filename:
        print("[WARN] No filename provided in request")
        return jsonify({"error": "No filename provided"}), 400

    blob_path = f"annotated/{filename}"
    try:
        blob = bucket.blob(blob_path)

        if not blob.exists():
            print(f"[WARN] File not found: {blob_path}")
            return jsonify({"error": "File not found"}), 404

        url = get_signed_url(blob_path)
        return jsonify({"image_url": url})

    except Exception as e:
        print(f"[ERROR] Exception in /get-image: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[INFO] Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)
