#!/usr/bin/env python

import pdal
import time
import sys, getopt
from pdb import set_trace

def main(argv):
    start = time.time()
    name=""
    bounds = []
    depth = 0
    mind = 14
    maxd = 15
    try:
        opts, args = getopt.getopt(argv,"hn:b:e:ms",["name=","bounds=","elevation=","mind","maxd"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    print "%s"%([opt for opt, arg in opts])
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif not len(opts) >= 3:
            print usage()
            sys.exit()
        elif opt in ("-n", "--name"):
            if len(arg)==0:
                print usage("name can not be empty")
                sys.exit()
            kml_name = arg
        elif opt in ("-b", "--bounds"):
            if arg == "[]":
                usage("bounds must be in format [xMin,yMin,xMax,yMax]")
            bounds = arg
        elif opt in ("-e", "--elevation"):
            if not arg > 0:
                usage("elevation must be greater than 0 meters.")
                sys.exit()
            elevation = arg
        elif opt in ("--maxd"):
            maxd = arg
        elif opt in ("--mind"):
            maxd = arg



    print("NAME: %s\nBounds: %s\nElevation:%s"%(kml_name,bounds,elevation))

def usage(err=""):
    print '\n'
    if len(err)>0:
        print("Error: %s\n\n"%(err))
    print '\
    Usage: queryLidar.py [OPTIONS] \n\
    Queries houston lidar service for ground/water points within\n\
    the bounding box and filters points based on the elevation\n\
    required. Using Delaunay Triangles, approximates a floodplain\n\
    for the requested elevation and returns an extruded KML set\n\
    to an absolute elevation rounded to the nearest meter.\n\n\
    -h              display this help and exit \n\n\
    The following arguments are required \n\
    -n, --name      name to be used when naming the output kml \n\
    -b, --bounds    bounding box in web mercator to devlop inundation.\n\
                    Required format [xMin,yMin,xMax,yMax] \n\
    -e, --elevation the elevation to develop a floodplain for in meters\n\n\
    The following arguments are optional\n\
    --mind          minimum octree depth requested (defaults to 14)\n\
    --maxd          maximum octree depth requested must be greater than\n\
                    \'--mind\' (defaults to 15)\n\n\n'
    return

if __name__ == "__main__":
   main(sys.argv[1:])
