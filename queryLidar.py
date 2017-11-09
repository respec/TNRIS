#!/usr/bin/env python

import pdal
import time
import sys, getopt
global kml_name, bounds, elevation, mind, maxd, altitudeMode, start

def main():
    # time our processes
    start = time.time()

    # parse user arguments
    parseOpts()

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

    # pipeline = pdal.Pipeline(unicode(pipeline_json))
    # pipeline.validate() # check if our JSON and options were good
    # count = pipeline.execute()
    # sys.stdout.write("Retrieval Complete: Count: %s in %s seconds\n" %(str(count),time.time()-start))
    # sys.stdout.flush()

    pipeline_json = """
    {
      "pipeline":[
        "laz/run.laz",
        {
          "type":"filters.python",
          "script": "py/inundation_filter.py",
          "function":"inundation",
          "module":"anything",
          "pdalargs":"{\\"elevation\\":%(elevation)s,\\"kml_name\\":\\"%(kml_name)s\\",\\"altitudeMode\\":\\"%(altitudeMode)s\\"}"
        }
      ]
    }"""%({"elevation":elevation,"kml_name":kml_name,"altitudeMode":altitudeMode})
    # print(pipeline_json)
    pipeline = pdal.Pipeline(unicode(pipeline_json))
    pipeline.validate() # check if our JSON and options were good
    # pipeline.loglevel = 8 #really noisy
    count = pipeline.execute()
    # arrays = pipeline.arrays
    # metadata = pipeline.metadata
    # log = pipeline.log

    print("Processing Complete: Count: %s in %s seconds\n" %(str(count),time.time()-start))

def parseOpts():
    global kml_name, bounds, elevation, mind, maxd, altitudeMode
    start = time.time()
    kml_name=""
    bounds = []
    elevation = 0
    mind = None
    maxd = None
    altitudeMode = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],"han:b:e:",["name=","bounds=","elevation=","mind=","maxd=","altitudeMode="])
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
            kml_name = arg
        elif opt in ("-b", "--bounds"):
            if arg == "[]":
                usage("bounds must be in format [xMin,yMin,xMax,yMax]")
            bounds = eval(arg)
        elif opt in ("-e", "--elevation"):
            if not arg > 0:
                usage("elevation must be greater than 0 meters.")
                sys.exit()
            elevation = float(arg)
        elif opt in ("--maxd"):
            maxd = int(arg)
        elif opt in ("--mind"):
            mind = int(arg)
        elif opt in ("-a", "--altitudeMode"):
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
    # print("NAME: %(name)s\nBounds: %(bounds)s\nElevation:%(elevation)s\nMinD:%(mind)s\nMaxD:%(maxd)s\nAltitudeMode:%(altitudeMode)s\n"%({'name':kml_name,'bounds':bounds,'elevation':elevation,'mind':mind,'maxd':maxd,'altitudeMode':altitudeMode}))

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
    -b, --bounds        bounding box in web mercator to devlop inundation.\n\
                        Required format [xMin,yMin,xMax,yMax] \n\
    -e, --elevation     the elevation to develop a floodplain for in meters\n\n\
    The following arguments are optional; however, \'--mind\' and \'maxd\'\n\
    must both be provided if the other is declared.\n\
    --mind              minimum octree depth requested (defaults to 14)\n\
    --maxd              maximum octree depth requested must be greater than\n\
                        \'--mind\' (defaults to 15)\n\n\
    -a, --altitudeMode  [ gnd | abs ] kml clamped to ground or absolute\n'
    return

if __name__ == "__main__":
   main()
