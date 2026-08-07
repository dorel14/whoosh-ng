"""Setup MinIO bucket for benchmarks."""

from __future__ import annotations

import boto3
from botocore.client import Config

ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET = "whoosh-benchmark"

client = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

try:
    client.create_bucket(Bucket=BUCKET)
    print(f"Bucket '{BUCKET}' created")
except client.exceptions.BucketAlreadyOwnedByYou:
    print(f"Bucket '{BUCKET}' already exists")

resp = client.list_objects_v2(Bucket=BUCKET)
print(f"Objects in bucket: {resp.get('KeyCount', 0)}")
