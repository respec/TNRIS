import sys, os

def inundation(ins,outs):
    from shapely.geometry import asMultiPoint,MultiPoint,Polygon,MultiPolygon, asPoint, Point, asPolygon
    from shapely.ops import cascaded_union
    import numpy as np
    import geopandas as gpd
    sys.path.append('/data/py')
    from alpha_shape import alpha_shape

    # default apt-get install version of geopandas is not complete. check for overlay function
    if not 'overlay' in dir(gpd):
        sys.stdout.write("\n\n**********\nOverlay function not in installed version of geopandas.\nRun pip install --upgrade geopandas to install.\n**********\n\n")
        sys.stdout.flush()
        return False


    elevation = pdalargs['elevation']
    outputName  = pdalargs['outputName']
    altitudeMode = pdalargs['altitudeMode']
    outputFileName = "%s_%sm" %(outputName,elevation)
    if altitudeMode == 'gnd':
        kml_to_create = "kml/%s_ground.kml"%(outputFileName)
        kml_doc_name = "%s (%sm Clamped to Ground)" %(outputName,elevation)
    else:
        kml_to_create = "kml/%s_absolute.kml"%(outputFileName)
        kml_doc_name = "%s (%sm Absolute)" %(outputName,elevation)

    crs = {'init':'epsg:3857'}

    # extract our x,y,z and stack
    np_array = np.column_stack((ins['X'],ins['Y'],ins['Z'],ins['Classification']))

    # # get our break down of classifications
    # classifications,counts = np.unique(ins['Classification'],return_counts=True)
    # f=open('Classification_Counts.txt','w')
    # f.write("%s"%(dict(zip(classifications, counts))))
    # f.close()

    below_array = np_array[(elevation >= np_array[:,2]) & (np_array[:,2] >= 0)][:,0:3]
    above_array = np_array[(elevation < np_array[:,2]) & (np_array[:,2] < (elevation + 3))][:,0:3] # arbitrary top filter (watch elevation of location)

    # # below floodplain
    # below_points = gpd.GeoSeries([i for i in asMultiPoint(below_array) if not i.is_empty])
    below_points = gpd.GeoSeries([Point(i) for i in below_array])
    below_points_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in below_points])
    below_points_gdf.to_file('shp/%s_below_points.shp'%(outputFileName))
    # fiona can't overwrite a geojson, remove first
    removeFile("geojson/%s_below_points.geojson"%(outputFileName))
    below_points_gdf.to_file('geojson/%s_below_points.geojson'%(outputFileName), driver='GeoJSON')
    sys.stdout.write("Below points successfully exported\n")
    sys.stdout.flush()

    flood_triangles = alpha_shape(gpd.GeoSeries([Point(i) for i in below_array[:,0:2]]),0.03)
    flood_triangles_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in flood_triangles[0] if not i.is_empty])
    flood_triangles_gdf.to_file('shp/%s_below_triangles.shp'%(outputFileName))
    sys.stdout.write("Below points successfully triangulated and exported\n")
    sys.stdout.flush()

    below_polygon = cascaded_union(flood_triangles_gdf.geometry)
    below_polygon_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in below_polygon if not i.is_empty])
    below_polygon_gdf.to_file('shp/%s_below_polygon.shp'%(outputFileName))
    sys.stdout.write("Below polygon successfully exported\n")
    sys.stdout.flush()


    # above floodplain
    above_points = gpd.GeoSeries([Point(i) for i in above_array])
    above_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in above_points])
    above_gdf.to_file('shp/%s_above_points.shp'%(outputFileName))
    # fiona can't overwrite a geojson, remove first
    removeFile("geojson/%s_above_points.geojson"%(outputFileName))
    above_gdf.to_file('geojson/%s_above_points.geojson'%(outputFileName), driver='GeoJSON')
    sys.stdout.write("Above points successfully exported\n")
    sys.stdout.flush()

    above_triangles = alpha_shape(gpd.GeoSeries([Point(i) for i in above_array[:,0:2]]),0.03)
    above_triangles_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in above_triangles[0] if not i.is_empty])
    above_triangles_gdf.to_file('shp/%s_above_triangles_0.03.shp'%(outputFileName))
    sys.stdout.write("Above points successfully triangulated and exported\n")
    sys.stdout.flush()

    above_polygon = cascaded_union(above_triangles_gdf.geometry)
    above_polygon_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in above_polygon if not i.is_empty])
    above_polygon_gdf.to_file('shp/%s_above_polygon.shp'%(outputFileName))
    sys.stdout.write("Above polygon successfully exported\n")
    sys.stdout.flush()

    # innundation = below_polygon_gdf.difference(above_polygon_gdf)
    inundation = gpd.overlay(below_polygon_gdf,above_polygon_gdf,how='difference')
    inundation_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i.buffer(-5,join_style=1).buffer(5,join_style=1) for i in inundation.geometry])
    inundation_gdf = inundation_gdf[inundation_gdf.is_empty==False]
    inundation_gdf.to_file('shp/%s_inundation.shp'%(outputFileName))

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
    for i in inundation_gdf.to_crs({'init': 'epsg:4326'}).geometry:
        p = kml.Placemark(ns, 'id', '%s meters'%(elevation))
        p.styleUrl = "#m_ylw-pushpin"
        # p.geometry =  i #Polygon([(0, 0, 0), (1, 1, 0), (1, 0, 1)])
        # p.geometry = Polygon((' 7.0))').join((' 7.0, ').join(i.wkt.split('((')[0].split(', ')).split('))')))
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
    sys.stdout.write("KML successfully created\n")
    sys.stdout.flush()
    return True


def removeFile(filename):
    try:
        os.remove(filename)
    except OSError:
        pass
