import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node # We only need the Node action
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share_path = get_package_share_directory('mdp_perception')

    # Arguments 
    config_arg = DeclareLaunchArgument(
        'config',
        default_value=os.path.join(pkg_share_path, 'config', 'perception.yml'),
        description='Path to the node-specific YAML config file'
    )
    image_topic_arg = DeclareLaunchArgument(
        'image_topic',
        default_value='/image_raw',
        description='The image topic for all perception nodes'
    )

    publish_annotated_arg = DeclareLaunchArgument(
        'publish_annotated',
        default_value='true',
        description='Whether to publish annotated images'
    )

    config_file = LaunchConfiguration('config')
    image_topic = LaunchConfiguration('image_topic')
    publish_annotated = LaunchConfiguration('publish_annotated')


    # Nodes

    # usb cam - replace later with mirte cam(s)
    usb_cam_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        parameters=[
            config_file,
            {'topic_name': image_topic}
        ]
    )

    # yolo node - integrate into containerized node when it is in c++ 
    object_detector_node = Node(
        package='mdp_perception',
        executable='object_detector_node.py',
        name='object_detector_node',
        output='screen',
        parameters=[
            config_file,
            {
                'image_topic': image_topic,
                'publish_annotated_image': publish_annotated
            }
        ]
    )
    # apriltag ... you get it. This is already in c++
    apriltag_detector_node = Node(
        package='mdp_perception',
        executable='apriltag_detector_node_exe',
        name='apriltag_detector_node',
        output='screen',
        parameters=[
            config_file,
            {
                'image_topic': image_topic,
                'publish_annotated_image': publish_annotated
            }
        ]
    )


    return LaunchDescription([
        config_arg,
        image_topic_arg,
        publish_annotated_arg,
        usb_cam_node,
        object_detector_node,
        apriltag_detector_node,
    ])