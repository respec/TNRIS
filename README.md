# tnris
TNRIS Project

1. Build docker image from docker/Dockerfile and run
```sh
cd ./docker/
docker build -t <image_name> .
docker run -it -v /drive/for/docker/to/mount:/docker/mount/location <image_name>:latest /bin/bash
# docker /data is a good mount location
```

2. Set the bounds in the *queryLidar.py* file and set the *depth* variable in the *py/innundation_filter.py*

3. Run queryLidar.py with bounds and depth input
```shell
./queryLidar.py -b <[xMin,yMin,xMax,yMax]> -d <depth in meters>
```

4. Retrieve kml output from *kml/innundation.kml*
