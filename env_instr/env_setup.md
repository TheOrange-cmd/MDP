Robostack typically needs a 2 stage install - first base robostack, then additional packages. 

Use the two environment files as follows below, mamba is highly recommended for speed. Modify your paths if appropriate. 

```
mamba env create -f "$HOME/Documents/GitHub/MDP/environment_base.yml"
mamba activate ros_env
mamba env update -f "$HOME/Documents/GitHub/MDP/environment_ros.yml"
```

When we want to add new packages, to keep things organized, do this. 

```
mamba install ros-humble-some-package      # try package 1
mamba install ros-humble-another-package   # try package 2
mamba install ros-humble-the-good-one      # try package 3 — this is the one
```

Then add to environment_ros.yml:

```
  - ros-humble-the-good-one
```

Update (clean) your environment if you want with:

```
mamba env update -f environment_ros.yml
```

And export for others convenience:
```
mamba env export --no-builds > environment_snapshot.yml
```

Or tell teammates to update with environment_ros.yml. 

