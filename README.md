# tnris
TNRIS Project

1. Build docker image from docker/Dockerfile and run
```sh
cd ./docker/
docker build -t <image_name> .
docker run -it -v /drive/for/docker/to/mount:/docker/mount/location <image_name>:latest /bin/bash
```

2. Set the bounds in the *queryLidar.py* file and set the *depth* variable in the *py/innundation_filter.py*

3. Run queryLidar.py
```shell
./queryLidar.py
```

4. Retrieve kml output from *kml/innundation.kml*
