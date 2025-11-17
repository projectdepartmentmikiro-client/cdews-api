import os
from flask import Flask, request, jsonify
from google.cloud import storage

BUCKET_NAME = os.environ.get("BUCKET_NAME")
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
SERVICE_ACCOUNT_FILE = "/opt/render/project/secrets/service_account.json"

client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
bucket = client.bucket(BUCKET_NAME)

app = Flask(__name__)

def get_signed_url(blob_name, expiration=3600):
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(version="v4", expiration=expiration, method="GET")

@app.route("/get-image", methods=["GET"])
def get_image():
    key = request.headers.get("x-api-key")
    secret = request.headers.get("x-api-secret")

    if key != API_KEY or secret != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    blob_path = f"annotated/{filename}"
    blob = bucket.blob(blob_path)
    if not blob.exists():
        return jsonify({"error": "File not found"}), 404

    url = get_signed_url(blob_path)
    return jsonify({"image_url": url})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
