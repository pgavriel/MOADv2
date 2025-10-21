# Manufacturing Objects & Assemblies Dataset v2 (MOADv2)   
[MOAD Data Pipeline](media/moadv2_pipeline.png)
This repository serves as an access point for the MOADv2 dataset. MOADv2 contains component data for NIST Assembly Task Boards (ATB) 1-4.  
   
Within the config folder, there is **objects.json** which defines which objects/sets are available for download, and **downloader_config.json** which allows you to configure which object set you would like to download, the folder to download to, and which types of object data you would like to download.  
Once **downloader_config.json** is configured as desired, simply run the downloader script via:   
*NOTE: It will prompt you to make sure everything looks correct before beginning the download.*  
```
cd MOADv2    
python3 scripts/download_moad.py   
```   
   
#### Downloadable Data Formats 
* **RGB** - Most objects were scanned in two different poses, and each pose contains 360 24 megapixel (6000x4000) images capturing all angles of the object. Captured using Canon Rebel SL3 DSLR cameras. This option also includes a **camera_config.json** file which describes the camera settings during capture, and **transforms.json** which defines the virtual camera pose for each image. *NOTE: This data (1.6GB / pose) takes a long time to download.*  
* **Pose Reconstruction** - The RGB images were used to train a NeRF reconstruction of each object scan, and this option will download a dense (5 million points) point cloud which was exported from that trained model.  
* **Realsense** - Each object pose also contains 360 colored pointclouds captured at 640x480 resolution, and transformed such that they all align with each other. Captured using Realsense D455 depth cameras.  
* **CAD Model** - CAD model of the object.  
* **Fused Model** - All data associated with multiple poses of the object being fused together to create complete object models.  
    * **Raw Cloud (.ply)** - This is the result of fusing the reconstruction pointclouds together from multiple poses to get a pointcloud of the entire object. All background points have been removed.  
    * **Raw Mesh (.ply)** - The result of applying Poisson surface reconstruction to the Raw Cloud.  
    * **OBJ Mesh** - Post processed mesh (cleaned, decimated, scaled to meter units), exported to an OBJ file format. Good for simulators like PyBullet.  
    * **USD Mesh** - Post processed mesh (cleaned, decimated, scaled to meter units), exported to an USD file format. Good for simulators like NVIDIA Omniverse, and Isaac Sim.  
    * **Blender File** - A .blend file containing the post processed version of the fused model, so the model can be further processed or exported to a different file format.  


#### Use Cases   
###### Object Reconstruction   
The high resolution RGB data combined with pre-computed camera transforms may be used to try alternative object reconstruction techniques.     

###### Synthetic Data Generation  
The provided model reconstructions may be used for generating synthetic training data using tools like Unity Perception or NVIDIA Omniverse Replicator. This data can be used for training object detection models, segmentation models, grasp planners, etc.    
  