import os
from flask import Flask, request, jsonify
from google.cloud import storage

SERVICE_KEY_JSON = "service.json"  # keep your service account JSON in the repo
BUCKET_NAME = "recieved_images-bucket"
API_KEY = "AKIA5FJ2QPLM7XN9T8QZSK:sk-proj-MjA3QlBqR1lqU1ZJTXp4TkpvQW5nSG9KVmQ2R3EyQ2x"

client = storage.Client.from_service_account_json(SERVICE_KEY_JSON)
bucket = client.bucket(BUCKET_NAME)

app = Flask(__name__)

def get_signed_url(blob_name, expiration=3600):
    """Generate signed URL for a blob in the bucket."""
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(version="v4", expiration=expiration, method="GET")

@app.route("/get-image", methods=["GET"])
def get_image():
    """Fetch image URL if API key is valid."""
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
