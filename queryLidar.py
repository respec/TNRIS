#!/usr/bin/env python

import pdal
import time
import sys, getopt
global outputName, bounds, boundsSrid, elevation, mind, maxd, altitudeMode, start

def main():
    # time our processes
    start = time.time()

    # parse user arguments
    parseOpts()

    checkBounds()

    minX = bounds[0]
    minY = bounds[1]
    minZ = 0
    maxX = bounds[2]
    maxY = bounds[3]
    maxZ = elevation + 3

    # get the data
    pipeline_json = """
    {
      "pipeline":[
        {
            "type": "readers.greyhound",
            "url": "aws.greyhound.io",
            "resource": "houston",
            "depth_begin":%(mind)s,
            "depth_end": %(maxd)s,
            "filter":{
                "Classification": {"$in":[2,9]}
            },
            "bounds":[%(minX)s,%(minY)s,%(minZ)s,%(maxX)s,%(maxY)s,%(maxZ)s]
        },
        {
          "type":"writers.las",
          "filename":"laz/run.laz"
        }
      ]
    }
    """ %({"minX":minX,"minY":minY,"minZ":minZ,"maxX":maxX,"maxY":maxY,"maxZ":maxZ,'mind':mind,'maxd':maxd})
    # print(pipeline_json)

    pipeline = pdal.Pipeline(unicode(pipeline_json))
    pipeline.validate() # check if our JSON and options were good
    count = pipeline.execute()
    if not count > 0:
        sys.stdout.write("\nNo points available for the elevation requested (%s meters).\nCheck the ground elevation of the area of interest and try again.\n\n"%(elevation))
        sys.stdout.flush()
        sys.exit()
    sys.stdout.write("Retrieval Complete: Count: %s in %s seconds\n" %(str(count),time.time()-start))
    sys.stdout.flush()

    pipeline_json = """
    {
      "pipeline":[
        "laz/run.laz",
        {
          "type":"filters.python",
          "script": "py/inundation_filter.py",
          "function":"inundation",
          "module":"anything",
          "pdalargs":"{\\"elevation\\":%(elevation)s,\\"outputName\\":\\"%(outputName)s\\",\\"altitudeMode\\":\\"%(altitudeMode)s\\"}"
        }
      ]
    }"""%({"elevation":elevation,"outputName":outputName,"altitudeMode":altitudeMode})
    # print(pipeline_json)
    pipeline = pdal.Pipeline(unicode(pipeline_json))
    pipeline.validate() # check if our JSON and options were good
    # pipeline.loglevel = 8 #really noisy
    count = pipeline.execute()
    # arrays = pipeline.arrays
    # metadata = pipeline.metadata
    # log = pipeline.log

    print("Processing Complete: Count: %s in %s seconds\n" %(str(count),time.time()-start))

def checkBounds():
    global bounds
    if boundsSrid == 0:
        # assume the bounds are in wgs84 as the pipeline expects
        return

    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point

    crs_to = {'init':'epsg:3857'}
    crs_from = {'init':'epsg:' + str(boundsSrid)} # http://spatialreference.org/ref/epsg/nad83-utm-zone-15n/ means srid of 26915 should translate directly to epsg

    pt_bottom_left = [bounds[0],bounds[1]]
    pt_top_right = [bounds[2],bounds[3]]
    pt_array = [pt_bottom_left,pt_top_right]
    bounds_shape_pts = [Point(i) for i in pt_array]
    bounds_geo_series = gpd.GeoSeries(bounds_shape_pts)
    bounds_geo_data_frame = gpd.GeoDataFrame(crs=crs_from,geometry=[i for i in bounds_geo_series])
    # project to desired crs
    bounds_geo_data_frame = bounds_geo_data_frame.to_crs(crs_to)
    # get the bounds
    new_bounds = bounds_geo_data_frame.geometry.bounds
    new_bounds_array = [new_bounds.minx.min(),new_bounds.miny.min(),new_bounds.maxx.max(),new_bounds.maxy.max()]
    bounds = new_bounds_array
    sys.stdout.write("Using re-projected bounds:\n" + str(new_bounds_array) + "\n\n")
    sys.stdout.flush()

def parseOpts():
    global outputName, bounds, boundsSrid, elevation, mind, maxd, altitudeMode
    start = time.time()
    outputName=""
    bounds = []
    boundsSrid = 0
    elevation = 0
    mind = None
    maxd = None
    altitudeMode = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hsan:b:e:",["name=","bounds=","srid=","elevation=","mind=","maxd=","altitudeMode="])
    except getopt.GetoptError:
        usage("Incorrect arguments provided")
        sys.exit(2)

    # # testing - print options and their values
    # print "%s"%([opt for opt, arg in opts])
    # print "%s"%([arg for opt, arg in opts])

    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif not len(opts) >= 3:
            print usage("Not enough arguments provided. Name, bounds and elevation are required.")
            sys.exit()
        elif opt in ("-n", "--name"):
            if len(arg)==0:
                print usage("Name can not be empty")
                sys.exit()
            outputName = arg
        elif opt in ("-b", "--bounds"):
            if arg == "[]":
                usage("bounds must be in format [xMin,yMin,xMax,yMax]")
            bounds = eval(arg)
        elif opt in ("-e", "--elevation"):
            if not arg > 0:
                usage("elevation must be greater than 0 meters.")
                sys.exit()
            elevation = float(arg)
        elif opt in ("-s", "--srid"):
            boundsSrid = int(arg)
        elif opt in ("--maxd"):
            maxd = int(arg)
        elif opt in ("--mind"):
            mind = int(arg)
        elif opt in ("-a", "--a", "--altitudeMode"):
            if not arg in ['gnd','abs']:
                usage("To set altitudeMode, the argument must either be \'gnd\' or \'abs\'")
                sys.exit()
            altitudeMode = arg

    # check mind and maxd values
    if mind==None and maxd==None:
        mind = 14
        maxd = 15
    elif (mind==None and maxd>0) or (mind>0 and maxd==None):
        usage ("If either \'--mind\' or \'--maxd\' is provided, the other must also be declared.")
        sys.exit()
    elif mind >= maxd:
        usage("Requested minimum octree depth (%s) cannot be greater\n       than or equal to the maximum octree depth(%s) requested."%(mind,maxd))
        sys.exit()

    # check altitudeMode and set default if needed
    if not altitudeMode:
        altitudeMode = "abs"

    # # print results for testing
    # print("NAME: %(name)s\nBounds: %(bounds)s\nElevation:%(elevation)s\nMinD:%(mind)s\nMaxD:%(maxd)s\nAltitudeMode:%(altitudeMode)s\n"%({'name':outputName,'bounds':bounds,'elevation':elevation,'mind':mind,'maxd':maxd,'altitudeMode':altitudeMode}))

def usage(err=""):
    print '\n'
    if len(err)>0:
        print("ERROR: %s\n\n"%(err))
    print '\
    Usage: queryLidar.py [OPTIONS] \n\
        Queries houston lidar service for ground/water points within\n\
        the bounding box and filters points based on the elevation\n\
        required. Using Delaunay Triangles, approximates a floodplain\n\
        for the requested elevation and returns an extruded KML set\n\
        to an absolute elevation rounded to the nearest meter.\n\n\
    -h              display this help and exit \n\n\
    The following arguments are required \n\
    -n, --name          name to be used when naming the output kml \n\
    -b, --bounds        bounding box (default in web mercator) to devlop inundation.\n\
                        Required format [xMin,yMin,xMax,yMax] \n\
    -e, --elevation     the elevation to develop a floodplain for in meters\n\n\
    The following arguments are optional; however, \'--mind\' and \'maxd\'\n\
    must both be provided if the other is declared.\n\
    --srid        the srid for the provided bounds (defaults to "4326" web mercator (WGS84) \n\
    --mind              minimum octree depth requested (defaults to 14)\n\
    --maxd              maximum octree depth requested must be greater than\n\
                        \'--mind\' (defaults to 15)\n\n\
    --a, --altitudeMode  [ gnd | abs ] kml clamped to ground or absolute\n'
    return

if __name__ == "__main__":
   main()
