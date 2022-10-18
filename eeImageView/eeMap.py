import ee
import folium

ee.Initialize()
class eeGetImage(folium.Map):
    """docstring for eeGetImage."""
    # @TODO eventually need to create methods for accessing the returned products
    def __init__(self, aoi, dates:tuple, cloud_perc=50):
        super(eeGetImage, self).__init__()
        self.aoi = aoi
        self.dates = dates
        self.cloud_perc = cloud_perc
        self.s1 = None
        self.s2 = None
        self.fc = None
        self._s1Collection = None
        # @ TODO move the above properties to protected

        fc = ee.FeatureCollection(aoi)
        s2 = self.__s2(fc, self.dates, self.cloud_perc)
        s1 = self.__s1(fc, self.dates)
        self._s1Collection = s1
        fc_geojson = fc.geometry().getInfo()

        # @TODO make this a dict will add a method to get image meta data
        # idea is to use the image ids to test against the and to access the eeImage Object directly
        # {Image_id: ee.Image(Image_id)}
        s2_id = self.__convert(s2)
        s1_id = self.__convert(s1)

        coords = fc.geometry().centroid(1).coordinates().getInfo()
        coords.reverse()

        s2_vis = {"min":0, "max": 3000, "bands":["B4", "B3", "B2"]}
        s1_vis = {"min":-25, "max":10, "bands":["VV"]}

        self.s2 = self.__tiledImage(s2_vis, coords, s2_id, fc_geojson)
        self.s1 = self.__tiledImage(s1_vis, coords, s1_id, fc_geojson)
    @property
    def S1Collection(self):
        return self._s1Collection

    def __s2(self, bounGeom, time:tuple, cloud_perc=50):
        img_col = ee.ImageCollection("COPERNICUS/S2").\
            filterDate(time[0], time[1]).\
            filterBounds(bounGeom).\
            filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_perc))
        return img_col

    def __s1(self, bounGeom, time:tuple):
        base_col = ee.ImageCollection("COPERNICUS/S1_GRD").\
            filterDate(time[0], time[1]).\
            filterBounds(bounGeom).\
            filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')).\
            filter(ee.Filter.eq('instrumentMode', 'IW')).\
            select(['VV', 'VH'])
        return base_col

    def __convert(self, img_col):
        return [img.get("id") for img in img_col.getInfo().get("features")]

    def __tiledImage(self, vis, coords, img_list, geom) -> folium.map:
        """This is used to display all images under the defined image collection in 
        a html fle
        
        Returns:
            folium.map -- returns a folium.map object
        """    
        counter = 0
        mapp = folium.Map(location=coords)
        for tile in img_list:
            image = ee.Image(tile)
            # fmtDate = date.format('Y-M-D').getInfo()
            mapIdDict = image.getMapId(vis)
            folium.TileLayer(
                tiles=mapIdDict['tile_fetcher'].url_format,
                attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
                overlay=True,
                control=True,
                name=f'{counter}: {str(tile)}',
            ).add_to(mapp)
            counter += 1
        folium.GeoJson(data=geom, name='aoi').add_to(mapp)
        mapp.add_child(folium.LayerControl(collapsed=False))
        return mapp