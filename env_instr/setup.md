git clone https://github.com/TheOrange-cmd/MDP.git
cd MDP/env_instr 
mamba env create -f "environment_base.yml" 
mamba activate ros_env 
mamba env update -f "environment_ros.yml"
cd ..
export MDP_ROOT=$(pwd)
cd mdp_ws
mamba activate ros_env 
# note, cmake-args were not necessary on my laptop but helped resolve a python not found error on my PC. 
colcon build --symlink-install \
  --packages-skip mirte_telemetrix_cpp \
  --packages-skip-by-dep mirte_telemetrix_cpp \
  --continue-on-error \
  --cmake-args \
    -DPython_ROOT_DIR=$CONDA_PREFIX \
    -DPython_EXECUTABLE=$CONDA_PREFIX/bin/python \
    -DPYTHON_EXECUTABLE=$CONDA_PREFIX/bin/python \
    -DPYTHON_INCLUDE_DIR=$CONDA_PREFIX/include/python3.11 \
    -DPYTHON_LIBRARY=$CONDA_PREFIX/lib/libpython3.11.so
source install/setup.bash
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$MDP_ROOT/mdp_ws/src/gazebo_apriltag/models:$MDP_ROOT/mdp_ws/src/mdp_worlds/models
# empty world:
ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml
# greenhouse world:
ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml world:=$MDP_ROOT/mdp_ws/src/mdp_worlds/worlds/greenhouse.world