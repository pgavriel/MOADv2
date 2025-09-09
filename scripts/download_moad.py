import os
from os.path import join
import json
import boto3

s3 = boto3.client("s3")
bucket_name = "your-bucket-name"
target_dir = "/path/to/downloads"

def download_file(s3_key, local_path):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    print(f"⬇️  Downloading s3://{bucket_name}/{s3_key} → {local_path}")
    s3.download_file(bucket_name, s3_key, local_path)

def download_prefix(prefix, local_root):
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            s3_key = obj["Key"]
            rel_path = os.path.relpath(s3_key, prefix)
            local_path = os.path.join(local_root, rel_path)
            download_file(s3_key, local_path)

def download_objects(config):
    for obj in config["objects"]:
        obj_prefix = f"{obj}/"

        # --- fused ---
        if config["include"].get("fused"):
            download_prefix(f"{obj_prefix}fused/", os.path.join(target_dir, obj, "fused"))

        # --- poses ---
        poses = config["include"].get("poses", {})
        for pose_name, items in poses.items():
            for item in items:
                s3_prefix = f"{obj_prefix}{pose_name}/{item}"
                local_path = os.path.join(target_dir, obj, pose_name, item)

                if "." in os.path.basename(item):  # file
                    download_file(s3_prefix, local_path)
                else:  # folder
                    download_prefix(s3_prefix + "/", local_path)


# === MAIN === 
# --- Load config and run ---
if __name__ == "__main__":
    script_path = os.path.realpath(__file__)
    script_directory = os.path.dirname(script_path)
    print(f"Script Dir: {script_directory}")
    config_directory = join(script_directory, "../config")
    print(f"Config Dir: {config_directory}")
    with open(join(config_directory, "downloader_config.json"), "r") as f:
        config = json.load(f)
    print(f"Config Loaded:\n{json.dumps(config, indent=4)}")
    # Load Object names
    with open(join(config_directory, "objects.json"), "r") as f:
        objects = json.load(f)
    print(f"Objects Master List:\n{json.dumps(objects, indent=4)}")
    
    # Assemble list of objects to download

    exit()
    # Download data
    download_objects(config)
