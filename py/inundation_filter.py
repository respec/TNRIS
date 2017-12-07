import sys, os
import zipfile
import time
import logging
logging.basicConfig()

sys.path.append('/data/py')
last = None

def inundation(ins,outs):
    """
    Function called by pdal pipeline to process points into an inundation KMZ
    """
    global start, last
    last = time.time()
    from shapely.geometry import Polygon, Point
    from shapely.ops import cascaded_union,unary_union
    import numpy as np
    import geopandas as gpd
    from geopandas.tools import sjoin
    from alpha_shape import alpha_shape

    # default apt-get install version of geopandas is not complete. check for overlay function
    if not 'overlay' in dir(gpd):
        sys.stdout.write("\n\n**********\nOverlay function not in installed version of geopandas.\nRun pip install --upgrade geopandas to install.\n**********\n\n")
        sys.stdout.flush()
        return False

    elevation = pdalargs['elevation']
    outputName  = pdalargs['outputName']
    altitudeMode = pdalargs['altitudeMode']
    start = float(pdalargs["start"])
    if pdalargs["writeLayers"] == "True":
        writeLayers = True
    else:
        writeLayers = False

    outputFileName = "%s_%sm" %(outputName,elevation)
    if altitudeMode == 'gnd':
        kml_to_create = "kml/%s_ground.kml"%(outputFileName)
        kmz_to_create = "kmz/%s_ground.kmz"%(outputFileName)
        kml_doc_name = "%s (%sm Clamped to Ground)" %(outputName,elevation)
    else:
        kml_to_create = "kml/%s_absolute.kml"%(outputFileName)
        kmz_to_create = "kmz/%s_absolute.kmz"%(outputFileName)
        kml_doc_name = "%s (%sm Absolute)" %(outputName,elevation)

    # default crs. needs to match data received from greyhound
    crs = {'init':'epsg:3857'}

    # extract our x,y,z and stack
    np_array = np.column_stack((ins['X'],ins['Y'],ins['Z'],ins['Classification']))

    # process points below the requested elevation
    below_array = np_array[(elevation >= np_array[:,2]) & (np_array[:,2] >= 0)][:,0:3]
    sys.stdout.write("1) Selection of below points complete\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
    sys.stdout.flush()

    # check that we have points before trying to do anything with them
    if len(below_array) < 1000:
        sys.stdout.write("\nThere are %s points falling below the requested elevation. Try a higher elevation.\n\n"%(len(below_array)))
        sys.stdout.flush()
        return False

    # create GDF with only x/y as we don't need z in the geometry (and can't have it for alpha shape function)
    below_points_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries([Point(i) for i in below_array[:,0:2]]))
    # manually set crs
    below_points_gdf.crs = crs
    sys.stdout.flush()
    if writeLayers:
        # export 3d points so new GDF with x/y/z
        below_points_z_gdf = gpd.GeoDataFrame(crs=crs,geometry=gpd.GeoSeries([Point(i) for i in below_array]))
        below_points_z_gdf.to_file('shp/%s_below_points.shp'%(outputFileName))
        # fiona can't overwrite a geojson, remove first
        removeFile("geojson/%s_below_points.geojson"%(outputFileName))
        below_points_z_gdf.to_file('geojson/%s_below_points.geojson'%(outputFileName), driver='GeoJSON')

    below_triangles = alpha_shape(below_points_gdf.geometry,0.03)
    below_triangles_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i.buffer(0) for i in below_triangles[0] if not i.is_empty])
    if writeLayers:
        below_triangles_gdf.to_file('shp/%s_below_triangles.shp'%(outputFileName))
    sys.stdout.write("1a) Below points successfully triangulated\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
    sys.stdout.flush()

    below_polygon = unary_union(below_triangles_gdf.geometry)
    below_polygon_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in below_polygon if not i.is_empty])
    if writeLayers:
        below_polygon_gdf.to_file('shp/%s_below_polygon.shp'%(outputFileName))
    sys.stdout.write("1b) Below polygon successfully dissolved\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
    sys.stdout.flush()

    # process points above requested elevation
    above_array = np_array[(elevation < np_array[:,2]) & (np_array[:,2] < (elevation + 3))][:,0:3] # arbitrary top filter (watch elevation of location)
    sys.stdout.write("2) Selection of above points complete\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
    sys.stdout.flush()

    # check that we have points before trying to do anything with them
    if len(above_array) < 1:
        sys.stdout.write("\nThere are %s points above the requested elevation. Not processing the above points and just exporting area below requested elevation.\n\n"%(len(above_array)))
        sys.stdout.flush()
        inundation_gdf = below_polygon_gdf
    else:
        # above floodplain
        above_points_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries([Point(i) for i in above_array[:,0:2]]))
        # manually set crs
        above_points_gdf.crs = crs
        sys.stdout.flush()
        if writeLayers:
            # export 3d points so new GDF with x/y/z
            above_points_z_gdf = gpd.GeoDataFrame(crs=crs,geometry=gpd.GeoSeries([Point(i) for i in above_array]))
            above_points_z_gdf.to_file('shp/%s_above_points.shp'%(outputFileName))
            # fiona can't overwrite a geojson, remove first
            removeFile("geojson/%s_above_points.geojson"%(outputFileName))
            above_points_z_gdf.to_file('geojson/%s_above_points.geojson'%(outputFileName), driver='GeoJSON')

        # # here we could filter above points for just those within X meters of initial below areas - *** UNTESTED ***
        # above_points_filtered = sjoin(above_points_gdf, below_polygon_gdf, how='left', op='intersects')
        # above_points_filtered_clean = above_points_filtered[above_points_filtered.index_right.isnull()]
        # above_points_filtered_clean_gdf = gpd.GeoDataFrame(crs=crs, geometry=[i.buffer(0) for i in above_points_filtered_clean.geometry if not i.is_empty])

        above_triangles = alpha_shape(above_points_gdf.geometry,0.03)
        above_triangles_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in above_triangles[0] if not i.is_empty])
        if writeLayers:
            above_triangles_gdf.to_file('shp/%s_above_triangles.shp'%(outputFileName))
        sys.stdout.write("2a) Above points successfully triangulated\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
        sys.stdout.flush()

        # select polygons above that intersect below points
        below_points_buffered = gpd.GeoDataFrame(crs=crs,geometry=below_points_gdf.buffer(1))
        if writeLayers:
            below_points_buffered.to_file('shp/%s_below_points_buffered.shp'%(outputFileName))
        sys.stdout.write("2b-1) Below points successfully buffered by 1m\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
        sys.stdout.flush()
        above_triangles_below = sjoin(above_triangles_gdf, below_points_buffered, how='left', op='intersects')

        # # use this if we want to only join points (not buffered points)
        # above_triangles_below = sjoin(above_triangles_gdf, below_points_gdf, how='left', op='intersects')

        above_triangles_clean = above_triangles_below[above_triangles_below.index_right.isnull()]
        above_triangles_clean_gdf = gpd.GeoDataFrame(crs=crs, geometry=[i.buffer(0) for i in above_triangles_clean.geometry if not i.is_empty])
        above_triangles_clean_union = unary_union(above_triangles_clean_gdf.geometry)
        above_triangles_clean_union_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in above_triangles_clean_union if not i.is_empty])
        if writeLayers:
            above_triangles_clean_gdf.to_file('shp/%s_above_triangles_clean.shp'%(outputFileName))
        sys.stdout.write("2b-2 - 2d) Above triangles coincident with below points(bufffered by 1) removed\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
        sys.stdout.flush()

        inundation = gpd.overlay(below_polygon_gdf,above_triangles_clean_union_gdf,how='difference')
        sys.stdout.write("3) Inundation layer created from difference of below polygon and cleaned above polygon\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
        sys.stdout.flush()
        inundation_smoothed = gpd.GeoSeries([i.buffer(-2,join_style=1).buffer(10,join_style=1).buffer(-8,join_style=1) for i in inundation.geometry])
        inundation_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i.buffer(0) for i in inundation_smoothed if not i.is_empty])
        inundation_clean_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in unary_union(inundation_gdf.geometry)])
        sys.stdout.write("4) Inundation layer smoothed\n     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
        sys.stdout.flush()
        if writeLayers:
            inundation_clean_gdf.to_file('shp/%s_inundation.shp'%(outputFileName))

    # build kml
    import fastkml
    from fastkml import kml,gx
    # Create the root KML object
    k = kml.KML()
    k.from_string(unicode(open('kml/template.kml').read()).encode('utf8'))
    ns = '{http://www.opengis.net/kml/2.2}'

    # # Find the KML Document and add it to our KML root object
    d = list(k.features())[0]
    d.name = kml_doc_name


    # Create a KML Folder and add it to the Document
    f = kml.Folder(ns, 'fid', 'Elevation %s'%(elevation), 'Polygons in this folder represent a flood elevation of %s meters'%(elevation))
    d.append(f)
    # Create a Placemark with a polygon geometry and add it to the folder

    # for i in below_polygon_gdf.to_crs({'init': 'epsg:4326'}).geometry:
    for i in inundation_clean_gdf.to_crs({'init': 'epsg:4326'}).geometry:
        p = kml.Placemark(ns, 'id', '%s meters'%(elevation))
        p.styleUrl = "#m_ylw-pushpin"
        vertices = []
        geom = fastkml.geometry.Geometry()
        for ii in i.exterior.coords:
            l = list(ii)
            l.append(elevation)
            vertices.append(tuple(l))
        geom.geometry = Polygon(vertices)
        p.geometry = geom
        f.append(p)


    # Print out the KML Object as a string
    f = open(kml_to_create,'w')
    if altitudeMode == "abs":
        addExtrude = "<extrude>1</extrude><altitudeMode>absolute</altitudeMode>"
    else:
        addExtrude = ""
    kmlString = k.to_string()
    f.write(kmlString.replace("<kml:Polygon>","<kml:Polygon>%s"%(addExtrude)))
    f.close()
    # create kmz from kml
    zipfile.ZipFile(kmz_to_create, mode='w').write(kml_to_create)
    sys.stdout.write("5) Inundation KML/KMZ (\"%s\") created\n"%(kmz_to_create.split("/")[1].split(".kmz")[0]) + "     - %s/%s seconds (last step/total).\n"%(eval(",".join([str(i) for i in toc()]))))
    sys.stdout.flush()

    return True


def removeFile(filename):
    """
    Simple function to remove file if it exists
    """
    try:
        os.remove(filename)
    except OSError:
        pass


def toc():
    """
    A simple function to take start/last time ans return array of time elapsed
    since last call and since process started
    """
    global last,start
    if last == None:
        timer = [None, round((time.time()-start),1)]
    else:
        timer = [round((time.time()-last),1), round((time.time()-start),1)]
    last = time.time()
    return timer
