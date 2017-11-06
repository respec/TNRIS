def inundation(ins,outs):
    import sys
    from shapely.geometry import asMultiPoint,MultiPoint,Polygon,MultiPolygon
    import numpy as np
    import geopandas as gpd
    sys.path.append('/data/py')
    from alpha_shape import alpha_shape

    depth = 6
    crs = {'init':'epsg:3857'}

    # extract our x,y,z and stack
    np_array = np.column_stack((ins['X'],ins['Y'],ins['Z'],ins['Classification']))

    # # get our break down of classifications
    # classifications,counts = np.unique(ins['Classification'],return_counts=True)
    # f=open('geopandas/log.log','w')
    # f.write("%s"%(dict(zip(classifications, counts))))
    # f.close()

    below_array = np_array[(depth >= np_array[:,2]) & (np_array[:,2] >= 0)][:,0:2]
    # above_array = np_array[(depth < np_array[:,2]) & (np_array[:,2] < 100)][:,0:2] # arbitrary top filter (watch elevation of location)

    # below floodplain
    below_points = gpd.GeoSeries([i for i in asMultiPoint(below_array)])
    below_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in below_points])
    below_gdf.to_file('shp/below_points.shp')
    flood = alpha_shape(below_gdf.geometry,0.035)
    flood_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in flood[0] if not i.is_empty]).to_crs({'init': 'epsg:4326'})
    flood_gdf.to_file('shp/below.shp')


    # # above floodplain
    # above_points = gpd.GeoSeries([i for i in asMultiPoint(above_array)])
    # above_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in above_points])
    # above_gdf.to_file('geopandas/above_points.shp')
    # high = alpha_shape(above_gdf.geometry,0.045)
    # high_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in high[0] if not i.is_empty])
    # high_gdf.to_file('geopandas/high_0.045.shp')

    # innundation = flood_gdf.difference(high_gdf)
    # gpd.GeoDataFrame(crs=crs,geometry=innundation).to_file('geopandas/innundation.shp')

    # # build kml
    from fastkml import kml
    # Create the root KML object
    k = kml.KML()
    k.from_string(unicode(open('kml/template.kml').read()).encode('utf8'))
    ns = '{http://www.opengis.net/kml/2.2}'

    # # Create a KML Document and add it to the KML root object
    # d = kml.Document(ns, 'docid', 'doc name', 'doc description')
    # k.append(d)
    # lookup the document tag
    d = list(k.features())[0]


    # Create a KML Folder and add it to the Document
    f = kml.Folder(ns, 'fid', 'f name', 'f description')
    d.append(f)

    # Create a Placemark with a polygon geometry and add it to the folder
    for i in flood_gdf.geometry:
        p = kml.Placemark(ns, 'id', 'name', 'description')
        p.styleUrl = "#m_ylw-pushpin"
        p.extrude = 1
        p.geometry =  i #Polygon([(0, 0, 0), (1, 1, 0), (1, 0, 1)])
        f.append(p)

    # Print out the KML Object as a string
    f = open('kml/inundation.kml','w')
    f.write(k.to_string())
    f.close()
    return True
