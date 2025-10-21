import os
from os.path import join
import json
import time
from datetime import timedelta
import boto3
from botocore import UNSIGNED
from botocore.client import Config

def folder_has_expected_files(local_dir, expected_count=360):
    """Check if a local directory already has the expected number of files."""
    if not os.path.isdir(local_dir):
        return False
    file_count = sum(1 for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f)))
    return file_count == expected_count



class MOADv2_Downloader:
    def __init__(self, config, object_list):
        self.config = config
        self.object_list = object_list
        
        # Setup target directory
        self.target_dir = config["target_directory"]
        print(f"Target Download Directory: {self.target_dir}")
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            print(f"Target Directory '{self.target_dir}' created or already exists.")
        except OSError as e:
            print(f"Error creating directory '{self.target_dir}': {e}")

        # Start S3 Client
        self.bucket_name = "moadv2"
        self.start_s3_client()

    def start_s3_client(self):
        if self.config["download_unsigned"]:
            # Anonymous S3 client (no credentials needed)
            self.s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
        else:
            self.s3 = boto3.client("s3")
        print("S3 Client Started...")

    def folder_exists(self, prefix):
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix if prefix.endswith('/') else prefix + '/',
            MaxKeys=1
        )
        return 'Contents' in response
    
    def list_pose_folders(self, obj_prefix):
        """
        Return a list of pose-* folder names for a given object prefix.
        """
        pose_folders = set()
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=obj_prefix, Delimiter="/"):
            for prefix in page.get("CommonPrefixes", []):
                folder_name = prefix["Prefix"].split("/")[-2]  # e.g., "pose-a"
                if folder_name.startswith("pose-"):
                    pose_folders.add(folder_name)
        return sorted(pose_folders)
    
    def download_file(self, s3_key, local_path):
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if os.path.exists(local_path):
            print(f"⏭️ Skipping {local_path} (already exists)",end="\t\t\t\r")
            return
        print(f"⬇️  Downloading s3://{self.bucket_name}/{s3_key} → {local_path}",end="\t\t\t\r")
        self.s3.download_file(self.bucket_name, s3_key, local_path)

    def download_prefix(self, prefix, local_root):
        file_found = False
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for obj in page.get("Contents", []):
                s3_key = obj["Key"]
                rel_path = os.path.relpath(s3_key, prefix)
                local_path = os.path.join(local_root, rel_path)
                self.download_file(s3_key, local_path)
                file_found = True
        if not file_found: print("File not found.")

    def download_objects(self):
        """
        Download datasets from S3 based on config rules.
        """
        data_cfg = self.config["data_to_download"]
        if data_cfg.get("rgb", False):
            print("WARNING: RGB data can take a long time to download, continue? (This can be configured in downloader_config.json)")
            input("YES: [Enter]\t\tNO: [Ctrl+C]")
            
        for obj in self.object_list:
            obj_name = obj
            download_start = time.time()
            obj_prefix = f"{obj}/"
            obj_local = os.path.join(self.target_dir, obj)
            print(f"\n📦 Processing object: {obj}")
            if not self.folder_exists(obj):
                print(f"❌ Folder not found in bucket: {obj}")
                continue

            # --- list pose folders dynamically ---
            pose_folders = self.list_pose_folders(obj_prefix)
            print(f"  Found poses: {pose_folders}")

            # --- RGB ---
            if data_cfg.get("rgb", False):
                print("\n  ▶ RGB data")
                for pose in pose_folders:
                    pose_prefix = f"{obj_prefix}{pose}/"
                    pose_local = os.path.join(obj_local, pose)
                    dslr_local = os.path.join(pose_local, "DSLR")
                    if folder_has_expected_files(dslr_local, expected_count=360):
                        print(f"⏭️ Skipping {dslr_local} (already has 360 files)")
                    else:
                        self.download_prefix(f"{pose_prefix}DSLR/", dslr_local)
                    # Get camera config file
                    s3_key = f"{pose_prefix}camera_config.json"
                    local_path = os.path.join(pose_local, "camera_config.json")
                    self.download_file(s3_key, local_path)
                    # Get camera transforms file
                    s3_key = f"{pose_prefix}transforms.json"
                    local_path = os.path.join(pose_local, "transforms.json")
                    self.download_file(s3_key, local_path)

            # --- NerF Cloud ---
            if data_cfg.get("pose_reconstruction", False):
                print("\n  ▶ Pose Reconstruction Pointcloud (Exported from NeRF)")
                for pose in pose_folders:
                    pose_prefix = f"{obj_prefix}{pose}/"
                    pose_local = os.path.join(obj_local, pose)
                    # self.download_prefix(f"{pose_prefix}DSLR/", os.path.join(pose_local, "DSLR"))
                    self.download_prefix(f"{pose_prefix}exports/", os.path.join(pose_local, "exports"))

            # --- Realsense ---
            if data_cfg.get("realsense", False):
                print("\n  ▶ Realsense data")
                for pose in pose_folders:
                    pose_prefix = f"{obj_prefix}{pose}/"
                    pose_local = os.path.join(obj_local, pose)
                    rs_local = os.path.join(pose_local, "realsense")
                    if folder_has_expected_files(rs_local, expected_count=360):
                        print(f"⏭️ Skipping {rs_local} (already has 360 files)")
                    else:
                        self.download_prefix(f"{pose_prefix}realsense/", rs_local)


            # --- CAD Model ---
            if data_cfg.get("cad_model", False):
                print("\n  ▶ CAD model")
                self.download_prefix(f"{obj_prefix}cad/", os.path.join(obj_local, "cad"))

            # --- Fused Model ---
            if "fused_model" in data_cfg:
                fused_cfg = data_cfg["fused_model"]
                if any(fused_cfg.values()): print("\n  ▶ Fused model")

                fused_prefix = f"{obj_prefix}fused/"
                fused_local = os.path.join(obj_local, "fused")

                # raw_cloud → fused/*_cloud.ply
                if fused_cfg.get("raw_cloud", False):
                    paginator = self.s3.get_paginator("list_objects_v2")
                    for page in paginator.paginate(Bucket=self.bucket_name, Prefix=fused_prefix):
                        for obj in page.get("Contents", []):
                            key = obj["Key"]
                            if key.endswith("_cloud.ply"):
                                rel_path = os.path.relpath(key, obj_prefix)
                                local_path = os.path.join(obj_local, rel_path)
                                self.download_file(key, local_path)

                # raw_mesh → fused/*_mesh.ply
                if fused_cfg.get("raw_mesh", False):
                    paginator = self.s3.get_paginator("list_objects_v2")
                    for page in paginator.paginate(Bucket=self.bucket_name, Prefix=fused_prefix):
                        for obj in page.get("Contents", []):
                            key = obj["Key"]
                            if key.endswith("_mesh.ply"):
                                rel_path = os.path.relpath(key, obj_prefix)
                                local_path = os.path.join(obj_local, rel_path)
                                self.download_file(key, local_path)

                # obj_mesh → all contents of fused/obj/
                if fused_cfg.get("obj_mesh", False):
                    self.download_prefix(f"{fused_prefix}obj/", os.path.join(fused_local, "obj"))

                # usd_mesh → all contents of fused/usd/
                if fused_cfg.get("usd_mesh", False):
                    self.download_prefix(f"{fused_prefix}usd/", os.path.join(fused_local, "usd"))

                # blender_file → all contents of fused/blender/
                if fused_cfg.get("blender_file", False):
                    self.download_prefix(f"{fused_prefix}blend/", os.path.join(fused_local, "blend"))
                    # baked_texture → single file fused/baked_texture.png - must be included for blender texture
                # if fused_cfg.get("baked_texture", False):
                    s3_key = f"{fused_prefix}baked_texture.png"
                    local_path = os.path.join(fused_local, "baked_texture.png")
                    self.download_file(s3_key, local_path)

            time_elapsed = time.time() - download_start
            print(f"\n\n✅ Finished {obj_name} in {timedelta(seconds=time_elapsed)}")
        print("\n\n== Finished All Objects ==")

# === MAIN === 
# --- Load config and run ---
if __name__ == "__main__":
    script_path = os.path.realpath(__file__)
    script_directory = os.path.dirname(script_path)
    print(f"Script Dir: {script_directory}")
    config_directory = join(script_directory, "../config")
    print(f"Config Dir: {config_directory}")

    # Load valid Object names
    with open(join(config_directory, "objects.json"), "r") as f:
        objects = json.load(f)
    print(f"Objects Master List:\n{json.dumps(objects, indent=4)}")

    with open(join(config_directory, "downloader_config.json"), "r") as f:
        config = json.load(f)
    print(f"Config Loaded:\n{json.dumps(config, indent=4)}")


    # Assemble list of objects to download data for
    to_download = config["objects_to_download"]
    if to_download in objects.keys():
        objects = objects[to_download]
        print(f"About to download {len(objects)} objects: ")
        for o in objects:
            print(f" > {o}")
        input("Continue?: (Ctrl+C to exit)")
    else:
        # TODO: Allow a list of specific object names to be passed
        print(f"Object list ID \"{to_download}\" not found in objects.json")
        exit()
    # Assemble list of objects to download
    downloader = MOADv2_Downloader(config,objects)

    # exit()
    # Download data
    total_start = time.time()
    downloader.download_objects()
    total_elapsed = time.time() - total_start
    print(f"\n🏁 All downloads complete in {timedelta(seconds=total_elapsed)}")
