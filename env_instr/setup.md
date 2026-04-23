git clone --recurse-submodules https://github.com/TheOrange-cmd/MDP.git 
cd MDP/env_instr 
mamba env create -f "environment_base.yml" 
mamba activate ros_env 
mamba env update -f "environment_ros.yml"
cd ..
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
cd ..

# empty world:
conda activate ros_env
cd mdp_ws/
source install/setup.bash
ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml

# greenhouse world: 
conda activate ros_env
cd mdp_ws/
source install/setup.bash
ros2 launch mdp_launch sim_full.launch.py 