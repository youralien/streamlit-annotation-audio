import streamlit as st
from google.cloud import storage
import json

@st.cache_resource
def get_gc_client():
    return storage.Client.from_service_account_info(st.secrets.googlecloud)

def save_dict_to_gcs(bucket_name, blob_name, data):
    # Convert Python dictionary to JSON string
    json_str = json.dumps(data)

    # Initialize GCS client
    client = get_gc_client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Upload the JSON string to GCS
    blob.upload_from_string(json_str, content_type='application/json')

def get_or_create_json_from_gcs(bucket_name, blob_name, credentials_dict):
    # Initialize GCS client
    client = storage.Client.from_service_account_info(credentials_dict)

    # Reference your bucket
    bucket = client.get_bucket(bucket_name)

    # Check if blob (JSON file) exists in the bucket
    if not storage.Blob(bucket=bucket, name=blob_name).exists(client):
        # If the blob doesn't exist, create an empty JSON blob in GCS
        empty_json = "{}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(empty_json, content_type='application/json')
        return {}
    else:
        # If the blob exists, download and return its contents
        blob = bucket.blob(blob_name)
        json_str = blob.download_as_text()
        data = json.loads(json_str)
        return data


def read_or_create_json_from_gcs(bucket_name, blob_name):
    # Initialize GCS client
    client = get_gc_client()
    bucket = client.get_bucket(bucket_name)

    if not storage.Blob(bucket=bucket, name=blob_name).exists(client):
        # If the blob doesn't exist, create an empty JSON blob in GCS
        empty_json = "{}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(empty_json, content_type='application/json')
        return {}

    else:
        blob = bucket.blob(blob_name)
        # Download the JSON string from GCS
        json_str = blob.download_as_text()
        # Convert JSON string to Python dictionary
        data = json.loads(json_str)
        return data

    return conv_new, speaker_new




# hard-coded setup
def setup():
    name = "alicja"
    data = {"examples": [67, 100], "current_example_ind": 0}
    save_dict_to_gcs("mh_annotations", f'{name}_global_dict.json',data)
#setup()