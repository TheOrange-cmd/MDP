import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.actions import SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


LAUNCH_DIR = os.path.dirname(os.path.realpath(__file__))
WS_ROOT = os.path.abspath(os.path.join(LAUNCH_DIR, '..', '..', '..', '..'))

def get_mirte_args():
    return [
        DeclareLaunchArgument('spawn_x', default_value='-2.590841'),
        DeclareLaunchArgument('spawn_y', default_value='-0.394920'),
        DeclareLaunchArgument('spawn_z', default_value='0.021444'),
        DeclareLaunchArgument('spawn_roll', default_value='0'),
        DeclareLaunchArgument('spawn_pitch', default_value='0'),
        DeclareLaunchArgument('spawn_yaw', default_value='-0.250000'),
        DeclareLaunchArgument('lidar_enable', default_value='true'),
        DeclareLaunchArgument('sonar_enable', default_value='true'),
        DeclareLaunchArgument('depth_camera_enable', default_value='true'),
    ]

def generate_launch_description():

    # Paths and package shares
    apriltag_models = os.path.join(WS_ROOT, 'mdp_ws', 'src', 'gazebo_apriltag', 'models')
    mdp_models = os.path.join(WS_ROOT, 'mdp_ws', 'src', 'mdp_worlds', 'models')
    
    set_model_path = SetEnvironmentVariable(
        'GAZEBO_MODEL_PATH',
        os.environ.get('GAZEBO_MODEL_PATH', '') + ':' + apriltag_models + ':' + mdp_models
    )

    mirte_gazebo_share = get_package_share_directory('mirte_gazebo')

    # Arguments
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=PathJoinSubstitution([
            FindPackageShare('mdp_worlds'), 'worlds', 'demo.world'
        ]),
        description='World file to load'
    )
    publish_annotated_arg = DeclareLaunchArgument(
        'publish_annotated',
        default_value='true'
    )

    gui_arg = DeclareLaunchArgument(
        'gui', 
        default_value='true'
    )




    # Launchers and nodes
    mirte_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(mirte_gazebo_share, 'launch', 'gazebo_mirte_master_empty.launch.xml')
        ),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'gui': LaunchConfiguration('gui'),
            'lidar_enable': LaunchConfiguration('lidar_enable'),
            'sonar_enable': LaunchConfiguration('sonar_enable'),
            'depth_camera_enable': LaunchConfiguration('depth_camera_enable'),
            'spawn_x': LaunchConfiguration('spawn_x'),
            'spawn_y': LaunchConfiguration('spawn_y'),
            'spawn_z': LaunchConfiguration('spawn_z'),
            'spawn_roll': LaunchConfiguration('spawn_roll'),
            'spawn_pitch': LaunchConfiguration('spawn_pitch'),
            'spawn_yaw': LaunchConfiguration('spawn_yaw'),
        }.items()
    )

    # Perception nodes
    object_detector_node = Node(
        package='mdp_perception',
        executable='object_detector_node.py',
        name='object_detector_node',
        output='screen',
        parameters=[{
            'publish_annotated_image': LaunchConfiguration('publish_annotated'),
            'use_sim_time': True
        }],
        remappings=[
            ('image_raw', '/camera/image_raw')
        ]
    )

    apriltag_detector_node = Node(
        package='mdp_perception',
        executable='apriltag_detector_node_exe',
        name='apriltag_detector_node',
        output='screen',
        parameters=[{
            'publish_annotated_image': LaunchConfiguration('publish_annotated'),
            'use_sim_time': True
        }],
        remappings=[
            ('image_raw', '/camera/image_raw')
        ]
    )

    # RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        parameters=[{'use_sim_time': True}],
        arguments=['-d' + os.path.join(get_package_share_directory('mdp_launch'), 'rviz', 'mdp.rviz')]
    )

    spawn_environment_node = Node(
        package='mdp_worlds',
        executable='spawn_environment.py',
        name='environment_spawner',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription(
        get_mirte_args() + [
        set_model_path,
        world_arg,
        publish_annotated_arg,
        gui_arg,
        mirte_launch,
        spawn_environment_node,
        object_detector_node,
        apriltag_detector_node,
        rviz_node,
    ])