# Makefile
sim:
	colcon build --symlink-install --packages-skip mirte_telemetrix_cpp --packages-skip-by-dep mirte_telemetrix_cpp

robot:
	colcon build --symlink-install

# greenhouse:
#     GAZEBO_MODEL_PATH=$(GAZEBO_MODEL_PATH):$(PWD)/src/gazebo_apriltag/models \
#     ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml world:=worlds/greenhouse.world