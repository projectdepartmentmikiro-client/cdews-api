import os
import json
from flask import Flask, request, jsonify
from google.cloud import storage

service_account_info = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
BUCKET_NAME = os.environ["BUCKET_NAME"]
API_KEY = os.environ["API_KEY"]

client = storage.Client.from_service_account_info(service_account_info)
bucket = client.bucket(BUCKET_NAME)

app = Flask(__name__)

def get_signed_url(blob_name, expiration=3600):
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(version="v4", expiration=expiration, method="GET")

@app.route("/get-image", methods=["GET"])
def get_image():
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    blob = bucket.blob(f"uploads/{filename}")
    if not blob.exists():
        return jsonify({"error": "File not found"}), 404

    url = get_signed_url(f"uploads/{filename}")
    return jsonify({"image_url": url})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
