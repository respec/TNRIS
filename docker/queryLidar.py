#!/usr/bin/env python

import pdal
import time

start = time.time()

# minX = -10595574.0414
# minY = 3467280.4304
# minZ = 0
# maxX = -10593437.2451
# maxY = 3468729.4304
# maxZ = 7

# get the data
pipeline_json = """
{
  "pipeline":[
    {
        "type": "readers.greyhound",
        "url": "aws.greyhound.io",
        "resource": "houston",
        "depth_begin":14,
        "depth_end": 18,
        "filter":{
            "Classification": {"$in":[1,2,9]}
        },
        "bounds":[-10599574.0414,3465280.4304,0,-10593437.2451,3468729.4304,8]
    },
    {
      "type":"writers.las",
      "filename":"laz/run.laz"
    }
  ]
}
"""

pipeline = pdal.Pipeline(unicode(pipeline_json))
pipeline.validate() # check if our JSON and options were good
count = pipeline.execute()
print("Retrieval Complete: Count: %s in %s seconds\n" %(str(count),time.time()-start))

json_src=open('py/py_pipe.json').read()
pipeline_json = unicode(json_src)
pipeline = pdal.Pipeline(pipeline_json)
pipeline.validate() # check if our JSON and options were good
# pipeline.loglevel = 8 #really noisy
count = pipeline.execute()
# arrays = pipeline.arrays
# metadata = pipeline.metadata
# log = pipeline.log

print("Processing Complete: Count: %s in %s seconds\n" %(str(count),time.time()-start))
