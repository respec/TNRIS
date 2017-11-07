# tnris
TNRIS Project

1. Build docker image from docker/Dockerfile and run
```sh
cd ./docker/
docker build -t <image_name> .
docker run -it -v /drive/for/docker/to/mount:/docker/mount/location <image_name>:latest /bin/bash
# docker /data is a good mount location
```

2. Make executible and run queryLidar.py with bounds and depth input
```shell
chmod +x queryLidar.py
# python queryLidar.py -b <[xMin,yMin,xMax,yMax]> -d <depth in meters>
./queryLidar.py -b [-10603019.1099,3478865.61026,-10595026.0129,3482627.59836] -d 8
```

3. Retrieve kml output from *kml/innundation.kml*
