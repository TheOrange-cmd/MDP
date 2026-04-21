Sensor noise process (note for later)The general workflow when you have the robot:
Measure: Place the robot stationary facing a flat wall at a known distance. Record LiDAR and depth camera data for ~60 seconds. The deviation from the known ground truth gives you your noise profile (mean and standard deviation).
Model: ROS sensor data typically shows Gaussian noise, so you'd compute mean and stddev from your samples.
Apply: Add a <noise> block to the relevant xacro. For the LiDAR in your modified .xacro:

xml<noise>
  <type>gaussian</type>
  <mean>0.0</mean>
  <stddev>0.01</stddev>  <!-- replace with measured value -->
</noise>
For the Orbbec, it goes inside the <camera> element in orbbec_astra_plus_pro.xacro. The stddev parameter is already in the macro signature but not wired in yet, so it's ready for this.