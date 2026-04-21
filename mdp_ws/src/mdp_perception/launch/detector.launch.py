import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share_path = get_package_share_directory('mdp_perception')

    # Argument to specify the config file
    config_arg = DeclareLaunchArgument(
        'config',
        default_value=os.path.join(pkg_share_path, 'config', 'obstacle_detector.yml'),
        description='Path to the YAML configuration file'
    )

    detector_node = Node(
        package='mdp_perception',
        executable='object_detector_node',
        name='object_detector_node',
        output='screen',
        parameters=[LaunchConfiguration('config')] 
    )

    usb_cam_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        output='screen',
        parameters=[{
            'video_device': '/dev/video4',
            'image_width': 640,
            'image_height': 480,
            'framerate': 30.0,
            'pixel_format': 'yuyv',
        }]
    )

    return LaunchDescription([
        config_arg,
        detector_node,
        usb_cam_node,
    ])