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
        "depth_begin":16,
        "depth_end": 17,
        "filter":{
            "Classification": {"$in":[2,9]}
        },
        "bounds":[-10591230.564,3468548.94503,0,-10587214.7986,3470568.17172,10]
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

json_src=open('json/pipeline.json').read()
pipeline_json = unicode(json_src)
pipeline = pdal.Pipeline(pipeline_json)
pipeline.validate() # check if our JSON and options were good
# pipeline.loglevel = 8 #really noisy
count = pipeline.execute()
# arrays = pipeline.arrays
# metadata = pipeline.metadata
# log = pipeline.log

print("Processing Complete: Count: %s in %s seconds\n" %(str(count),time.time()-start))
