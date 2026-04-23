#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SpawnEntity
import math # Needed for pi

# SDF for a simple box
BOX_SDF = """<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <static>true</static>
    <link name="link">
      <visual name="vis">
        <geometry><box><size>{sx} {sy} {sz}</size></box></geometry>
        <material><ambient>{r} {g} {b} 1</ambient></material>
      </visual>
      <collision name="col">
        <geometry><box><size>{sx} {sy} {sz}</size></box></geometry>
      </collision>
    </link>
  </model>
</sdf>"""

# SDF for the planter with a CORRECTLY ORIENTED AprilTag
# The visual's pose now includes a 180-degree yaw rotation (3.14159)
# to make the tag face outwards.
PLANTER_WITH_TAG_SDF = f"""<?xml version="1.0"?>
<sdf version="1.7">
  <model name="planter_l1">
    <static>true</static>
    <link name="link">
        <collision name="col">
            <geometry><box><size>2.0 0.4 0.4</size></box></geometry>
        </collision>
        <visual name="vis">
            <geometry><box><size>2.0 0.4 0.4</size></box></geometry>
            <material><ambient>0.3 0.5 0.2 1</ambient></material>
        </visual>
        <visual name="apriltag_vis">
            <pose>-1.001 0 0 0 0 0</pose>
            <geometry><box><size>0.001 0.15 0.15</size></box></geometry>
            <material>
                <script>
                    <uri>model://Apriltag36_11_00000/materials/scripts</uri>
                    <uri>model://Apriltag36_11_00000/materials/textures</uri>
                    <name>Apriltag36_11_00000</name>
                </script>
            </material>
        </visual>
    </link>
  </model>
</sdf>"""

# SDF for including a model from the Gazebo model database
INCLUDE_SDF = """<?xml version="1.0"?>
<sdf version="1.6">
  <include>
    <uri>model://{model_name}</uri>
  </include>
</sdf>"""

# List of all models to spawn, now consolidated
# Each dictionary contains all info needed to spawn it.
MODELS_TO_SPAWN = [
    # Planters (as simple boxes)
    dict(type='box', name="planter_l2",   x=2.5, y=-1.0, z=0.2, sx=2.0, sy=0.4, sz=0.4, r=0.3, g=0.5, b=0.2),
    dict(type='box', name="planter_r1",   x=0.0,   y=1.0,  z=0.2, sx=2.0, sy=0.4, sz=0.4, r=0.3, g=0.5, b=0.2),
    dict(type='box', name="planter_r2",   x=2.5, y=1.0,  z=0.2, sx=2.0, sy=0.4, sz=0.4, r=0.3, g=0.5, b=0.2),
    # Clutter
    dict(type='box', name="clutter_box1", x=1.5, y=0.2,  z=0.1, sx=0.3, sy=0.2, sz=0.2, r=0.6, g=0.4, b=0.1),
    # Planter with AprilTag (using custom SDF)
    dict(type='custom', name="planter_l1", xml=PLANTER_WITH_TAG_SDF, x=0.0, y=-1.0, z=0.2),
    # Human from Gazebo Models (using include)
    dict(type='include', name="human_obstacle", model_name="person_standing", x=3.0, y=0.0, z=0.0),
]

def main():
    rclpy.init()
    node = Node('environment_spawner')
    client = node.create_client(SpawnEntity, '/spawn_entity')

    node.get_logger().info('Waiting for /spawn_entity service...')
    while not client.wait_for_service(timeout_sec=1.0):
        node.get_logger().info('Still waiting for /spawn_entity service...')

    node.get_logger().info('Service is available. Spawning models in parallel...')
    
    # --- Parallel Spawning Logic ---
    futures = []
    for model in MODELS_TO_SPAWN:
        req = SpawnEntity.Request()
        req.name = model['name']
        
        if model['type'] == 'box':
            req.xml = BOX_SDF.format(**model)
        elif model['type'] == 'custom':
            req.xml = model['xml']
        elif model['type'] == 'include':
            req.xml = INCLUDE_SDF.format(**model)

        req.initial_pose.position.x = float(model['x'])
        req.initial_pose.position.y = float(model['y'])
        req.initial_pose.position.z = float(model['z'])

        # Call async and store the future object without waiting
        future = client.call_async(req)
        futures.append((model['name'], future))

    # Now, wait for all the stored futures to complete
    for name, future in futures:
        rclpy.spin_until_future_complete(node, future)
        if future.result() is not None:
            node.get_logger().info(f"Spawned {name}: {future.result().status_message}")
        else:
            node.get_logger().error(f"Failed to spawn {name}: {future.exception()}")
    # --- End of Parallel Spawning Logic ---

    node.get_logger().info('Environment spawning complete.')
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()