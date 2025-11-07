import os
import argparse
from pathlib import Path

URDF_TEMPLATE = """<?xml version="0.0" ?>
<robot name="{robot_name}">
  <link name="baseLink">
    <contact>
      <friction_anchor/>
      <lateral_friction value="0.8"/>
      <spinning_friction value="0.001"/>
      <rolling_friction value="0.001"/>
      <contact_cfm value="0.0"/>
      <contact_erp value="0.2"/>
    </contact>
    <inertial>
       <origin rpy="0 0 0" xyz="0 0 0"/>
       <mass value="0.01"/>
       <inertia ixx="1e-3" ixy="0" ixz="0" iyy="1e-3" iyz="0" izz="1e-3"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0"/>
      <geometry>
        <mesh filename="obj/fused_model.obj" scale="1 1 1"/>
      </geometry>
      <material name="white">
        <color rgba="1. 1. 1. 1."/>
      </material>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0"/>
      <geometry>
        <mesh filename="obj/fused_model.obj" scale="1 1 1"/>
      </geometry>
    </collision>
  </link>
</robot>
"""

def main():
    # Parse command line inputs
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, default=Path("data"))
    args = parser.parse_args()

    if not args.folder.exists():
        raise RuntimeError(f"Root dir does not exist: {args.folder}")

    for item in args.folder.iterdir():
        if not item.is_dir():
            continue
            
        folder_name = item.name

        fused_dir = item / "fused"
        # Check if fused dir exists
        if not os.path.exists(fused_dir):
            print(f"\033[33m[ERROR] 'fused' directory does not exist for {item}.\033[0m]")
            continue

        # Create filename based on object folder name
        urdf_filename = f"{folder_name}.urdf"
        urdf_path = fused_dir / urdf_filename

        urdf_text = URDF_TEMPLATE.format(robot_name=folder_name)

        # write urdf
        urdf_path.write_text(urdf_text)
        print(f"Created: {urdf_path}")

if __name__ == "__main__":
    main()
