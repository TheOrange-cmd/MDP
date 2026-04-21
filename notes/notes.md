April tags 
Plant detection 
HRI
human obstacle detection on board 
navigation and mapping 

Optimization: look into writing critical nodes in c++ and ComposableNodeContainers to share sensor data for high efficiency 

Note, replaced lines 21-22 in mdp_ws/src/mirte-ros-packages/mirte_control/mirte_master_base_control/bringup/config/mirte_base_control.yaml

Changed line 83 in /home/daniel/Documents/GitHub/MDP/mdp_ws/src/mirte-ros-packages/mirte_description/mirte_master_description/urdf/lidar.xacro from 10 to 5. 

Changed line 63 in /home/daniel/Documents/GitHub/MDP/mdp_ws/src/mirte-ros-packages/mirte_description/mirte_master_description/urdf/ultrasonic.xacro from 30 to 10. 

Replaced gazebo section in /home/daniel/Documents/GitHub/MDP/mdp_ws/src/mirte-ros-packages/mirte_description/mirte_master_description/urdf/lidar.xacro

The default teleop has no repeat parameter so the robot will pause for a moment during simulation after you command a move. 

Fix with:

ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  --remap cmd_vel:=/mirte_base_controller/cmd_vel_unstamped \
  -p repeat_rate:=10.0

To add apriltags in the world, modify mdp_ws/src/mirte-gazebo/launch/gazebo_mirte_world_generated.launch.xml:

<set_env name="GAZEBO_MODEL_PATH" value="$(env GAZEBO_MODEL_PATH ''):$(find-pkg-share mirte_gazebo)/models:$(find-pkg-share mirte_gazebo)/../../../src/gazebo_apriltag/models"/>