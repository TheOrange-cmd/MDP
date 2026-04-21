To run, execute:

```
mamba activate ros_env
cd mdp_ws
rm -rf install/ build/ log/  # clean build
colcon build --packages-select mdp_perception # build perception package
source install/setup.bash
ros2 launch mdp_perception detector.launch.py
```

Or in one go assuming you're in mdp_ws and activated the env

```
rm -rf install/ build/ log/ && colcon build --packages-select mdp_perception && source install/setup.bash && ros2 launch mdp_perception detector.launch.py

# or:

rm -rf install/ build/ log/ && colcon build --packages-select mdp_perception && source install/setup.bash && ros2 launch mdp_perception perception.launch.py
```

In another terminal, open rviz and view the annotated image:

```
mamba activate ros_env
cd mdp_ws
source install/setup.bash
rviz2
```

Then add the topic views for /image_raw and /detections/annotated_image. 


To run the sim, use either the empty world:
source install/setup.bash
ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml 

Or the greenhouse world:
First set the apriltags path - check this is initialized correctly first! 
export GAZEBO_MODEL_PATH="$GAZEBO_MODEL_PATH:$ws/src/gazebo_apriltag/models"
source install/setup.bash
ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml world:=worlds/greenhouse.world