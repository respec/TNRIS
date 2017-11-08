def inundation(ins,outs):
    import sys
    from shapely.geometry import asMultiPoint,MultiPoint,Polygon,MultiPolygon, asPoint, Point, asPolygon
    from shapely.ops import cascaded_union
    import numpy as np
    import geopandas as gpd
    sys.path.append('/data/py')
    from alpha_shape import alpha_shape


    depth = int(round(pdalargs['depth'],0))
    crs = {'init':'epsg:3857'}

    # extract our x,y,z and stack
    np_array = np.column_stack((ins['X'],ins['Y'],ins['Z'],ins['Classification']))

    # # get our break down of classifications
    # classifications,counts = np.unique(ins['Classification'],return_counts=True)
    # f=open('Classification_Counts.txt','w')
    # f.write("%s"%(dict(zip(classifications, counts))))
    # f.close()

    below_array = np_array[(depth >= np_array[:,2]) & (np_array[:,2] >= 0)][:,0:2]
    # above_array = np_array[(depth < np_array[:,2]) & (np_array[:,2] < 100)][:,0:3] # arbitrary top filter (watch elevation of location)

    # below floodplain
    # below_points = gpd.GeoSeries([Point(i) for i in below_array])
    below_points = gpd.GeoSeries([i for i in asMultiPoint(below_array) if not i.is_empty])
    below_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in below_points])
    below_gdf.to_file('shp/below_points.shp')
    flood_triangles = alpha_shape(below_gdf.geometry,0.035)
    flood = cascaded_union(triangles)
    flood_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in flood[0] if not i.is_empty]).to_crs({'init': 'epsg:4326'})
    flood_gdf.to_file('shp/below.shp')


    # # above floodplain
    # above_points = gpd.GeoSeries([Point(i) for i in above_array])
    # above_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in above_points])
    # above_gdf.to_file('shp/above_points.shp')
    # high = alpha_shape(above_gdf.geometry,0.035)
    # high_gdf = gpd.GeoDataFrame(crs=crs,geometry=[i for i in high[0] if not i.is_empty])
    # high_gdf.to_file('shp/above.shp')

    # innundation = flood_gdf.difference(high_gdf)
    # gpd.GeoDataFrame(crs=crs,geometry=innundation).to_file('shp/innundation.shp')

    # # build kml
    import fastkml
    from fastkml import kml,gx
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
    f = kml.Folder(ns, 'fid', 'Depth %s'%(depth), 'Polygons in this folder represent a flood depth of %s meters'%(depth))
    d.append(f)
    # Create a Placemark with a polygon geometry and add it to the folder
    for i in flood_gdf.geometry:
        p = kml.Placemark(ns, 'id', '%s meters'%(depth))
        p.styleUrl = "#m_ylw-pushpin"
        # p.geometry =  i #Polygon([(0, 0, 0), (1, 1, 0), (1, 0, 1)])
        # p.geometry = Polygon((' 7.0))').join((' 7.0, ').join(i.wkt.split('((')[0].split(', ')).split('))')))
        vertices = []
        geom = fastkml.geometry.Geometry()
        for ii in i.exterior.coords:
            l = list(ii)
            l.append(depth)
            vertices.append(tuple(l))
        geom.geometry = Polygon(vertices)
        # geom.extrude=True
        # geom.altitudeMode="absolute"
        p.geometry = geom
        f.append(p)


    # Print out the KML Object as a string
    f = open('kml/inundation.kml','w')
    addExtrude = "<extrude>1</extrude><altitudeMode>absolute</altitudeMode>"
    kmlString = k.to_string()
    f.write(kmlString.replace("<kml:Polygon>","<kml:Polygon>%s"%(addExtrude)))
    f.close()
    return True
