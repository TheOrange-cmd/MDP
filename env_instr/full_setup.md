# MDP Project Setup

## Prerequisites
- Ubuntu installed
- Miniforge/Mambaforge installed

## 1. Create Conda Environment
cd to project root, then:
    mamba env create -f environment_base.yml
    mamba activate ros_env
    mamba env update -f environment_ros.yml

## 2. Clone Mirte Packages
    mkdir -p mdp_ws/src && cd mdp_ws
    git clone https://github.com/[your-fork]/mirte-gazebo src/mirte-gazebo
    vcs import src/ < src/mirte-gazebo/sources.repos
    cd src/mirte-ros-packages && git submodule update --init --recursive && cd ../..

Note: use our fork of mirte-gazebo and mirte-ros-packages, not the originals,
as we have applied fixes for ros2_controllers compatibility and Gazebo Classic
sensor plugin API changes.

## 3. Clone AprilTag Models
    cd src
    git clone https://github.com/koide3/gazebo_apriltag
    cd ..

## 4. Build
    make sim
    # equivalent to:
    # colcon build --symlink-install \
    #   --packages-skip mirte_telemetrix_cpp \
    #   --packages-skip-by-dep mirte_telemetrix_cpp

## 5. Environment Setup
Source this before every session (or add to your shell rc):
    source setup.sh

The setup.sh contains:
    export GAZEBO_PLUGIN_PATH=$CONDA_PREFIX/lib:$GAZEBO_PLUGIN_PATH
    export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/lib:$CONDA_PREFIX/lib:$CONDA_PREFIX/opt/rviz_ogre_vendor/lib
    export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$(pwd)/src/gazebo_apriltag/models
    source $(pwd)/install/setup.bash

## 6. Run
Empty world:
    ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml

Greenhouse world:
    ros2 launch mirte_gazebo gazebo_mirte_master_empty.launch.xml \
      world:=worlds/greenhouse.world

Teleoperation (in a second terminal, after sourcing setup.sh):
    ros2 run teleop_twist_keyboard teleop_twist_keyboard \
      --ros-args --remap cmd_vel:=/mirte_base_controller/cmd_vel_unstamped