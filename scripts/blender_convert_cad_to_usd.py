import bpy
import os
import sys

# -----------------------
# Parse command line args
# -----------------------
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]  # everything after --
else:
    argv = []

if len(argv) < 1:
    raise ValueError("Usage: blender --background --python script.py -- /path/to/input_file")

input_mesh = os.path.abspath(argv[0])
input_dir = os.path.dirname(input_mesh)
# Output dir -- save to same directory
output_dir = input_dir

# -----------------------
# SETTINGS 
# -----------------------
scale_factor = 0.001
model_color = (207, 159, 255,255)


# -----------------------
# Clean scene
# -----------------------
print("Cleaning Scene...")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# -----------------------
# Import mesh
# -----------------------
print(f"Importing mesh... \"{input_mesh}\"")

# bpy.ops.preferences.addon_enable(module="io_mesh_ply")
# bpy.ops.import_mesh.ply(filepath=input_mesh)
bpy.ops.wm.stl_import(filepath=input_mesh)
obj = bpy.context.selected_objects[0]
obj.scale = (scale_factor, scale_factor, scale_factor)

# Delete all other objects
for o in bpy.data.objects:
    if o != obj:
        bpy.data.objects.remove(o, do_unlink=True)

# -----------------------
# Set origins
# -----------------------
print("Fixing Origin...")
bpy.context.view_layer.objects.active = obj
bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')

## ADD TEXTURE/MATERIAL
# Create material
mat = bpy.data.materials.new(name="SolidColorMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = model_color
    bsdf.inputs["Roughness"].default_value = 0.4
    bsdf.inputs["Metallic"].default_value = 0.0

# Assign material to object
if len(obj.data.materials):
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)




# -----------------------
# Export USD & OBJ
# -----------------------
usd_path = os.path.join(output_dir, "converted_cad.usd")

# https://docs.blender.org/api/current/bpy.ops.wm.html#bpy.ops.wm.usd_export 
bpy.ops.wm.usd_export(filepath=usd_path,check_existing=True)
# bpy.ops.export_scene.usd(filepath=usd_path, selected_objects=True)
# bpy.ops.export_scene.obj(filepath=obj_path, use_selection=True)
# https://docs.blender.org/api/current/bpy.ops.wm.html#bpy.ops.wm.usd_export
# bpy.ops.wm.obj_export(filepath=obj_path,check_existing=True,path_mode="COPY")

print("✅ Processing complete!")
print(f"USD:   {usd_path}")