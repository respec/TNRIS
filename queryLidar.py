#!/usr/bin/env python

import pdal
import time
import sys, getopt

def main(argv):
    start = time.time()
    bounds = []
    depth = 0
    try:
      opts, args = getopt.getopt(argv,"hb:d:",["bounds=","depth="])
    except getopt.GetoptError:
      print 'queryLidar.py -b [xMin,yMin,xMax,yMax] -d <depth(m...)>'
      sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'queryLidar.py -b [xMin,yMin,xMax,yMax] -d <depth(m)>'
            sys.exit()
        elif opt in ("-b", "--bounds"):
            bounds = arg
        elif opt in ("-d", "--depth"):
            depth = arg
        elif bounds==[] or depth==0:
            print 'queryLidar.py -b [xMin,yMin,xMax,yMax] -d <depth(m)>'
            sys.exit()

    minX = eval(bounds)[0]
    minY = eval(bounds)[1]
    minZ = 0
    maxX = eval(bounds)[2]
    maxY = eval(bounds)[3]
    maxZ = int(round(eval(depth),0)) + 5

    # get the data
    pipeline_json = """
    {
      "pipeline":[
        {
            "type": "readers.greyhound",
            "url": "aws.greyhound.io",
            "resource": "houston",
            "depth_begin":14,
            "depth_end": 15,
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
    """ %({"minX":minX,"minY":minY,"minZ":minZ,"maxX":maxX,"maxY":maxY,"maxZ":maxZ})
    # print(pipeline_json)

    pipeline = pdal.Pipeline(unicode(pipeline_json))
    pipeline.validate() # check if our JSON and options were good
    count = pipeline.execute()
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
          "pdalargs":"{\\"depth\\":%(depth)s}"
        }
      ]
    }"""%({"depth":depth})
    # print(pipeline_json)
    pipeline = pdal.Pipeline(unicode(pipeline_json))
    pipeline.validate() # check if our JSON and options were good
    # pipeline.loglevel = 8 #really noisy
    count = pipeline.execute()
    # arrays = pipeline.arrays
    # metadata = pipeline.metadata
    # log = pipeline.log

    print("Processing Complete: Count: %s in %s seconds\n" %(str(count),time.time()-start))

if __name__ == "__main__":
   main(sys.argv[1:])
