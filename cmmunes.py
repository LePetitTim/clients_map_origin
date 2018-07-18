import requests
from bs4 import BeautifulSoup
import shutil
import csv
from shapely.geometry import shape, mapping
from shapely.ops import cascaded_union
import fiona
import json

dep = "05"
values = ["Guillestre", "Eygliers", "Risoul", "Saint-Crépin", "Vars", "Réotier", "Saint-Clément-sur-Durance", "Mont-Dauphin"]
geom = []

for value in values:
    with requests.Session() as s:
        download = s.get('https://public.opendatasoft.com/explore/dataset/correspondance-code-insee-code-postal/download/?format=csv&q='+ value +'&timezone=Europe/Berlin&use_labels_for_header=true')
        decoded_content = download.content.decode('utf-8')
        cr = csv.DictReader(decoded_content.splitlines(), delimiter=';')
        my_list = list(cr)
        for row in my_list:
            if row["Code Département"] == dep:
                geom.append(shape(json.loads(row["geo_shape"])))

multi = cascaded_union(geom)

with fiona.open('test.shp', 'w', 'ESRI Shapefile', {'geometry': 'MultiPolygon', 'properties': [('id', 'int'), ('name', "str")]}) as c:
    c.write({'geometry': mapping(multi), 'properties': {'id': 1, 'name': "OIE"}})