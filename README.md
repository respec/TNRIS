# TNRIS
TNRIS Project

1. Build docker image from docker/Dockerfile and run
```sh
cd ./docker/
sudo docker build -t <image_name> .
sudo docker run -it -v [local path the git repo]:/data <image_name>:latest /bin/bash
# Script currently assumes /data
```

2. Make executible and run queryLidar.py with bounds and depth input
```shell
cd /data
chmod +x queryLidar.py
# python queryLidar.py -b <[xMin,yMin,xMax,yMax]> -d <depth in meters>
./queryLidar.py -b [-10603019.1099,3478865.61026,-10595026.0129,3482627.59836] -d 8
```

3. Retrieve kml output from *kml/innundation.kml*
