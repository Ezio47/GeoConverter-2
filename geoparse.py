import csv
import json
import geojson #must install :(
import matplotlib.path as mplPath # must install
import geoconverter 
import SPECIES_DICT as sp

def parse_csv(raw_file):
	""" Opens .CSV raw_file, returns parsed_data as JSON"""
	open_file = open(raw_file)
	csv_file = csv.reader(open_file, delimiter = ",")
	fields = csv_file.next()
	
	parsed_data = []
	for row in csv_file:
		parsed_data.append(dict(zip(fields, row)))

	open_file.close()

	return parsed_data

def parse_json(data):
	"""Parse JSON format to .CSV for export"""
	header = []
	for h in data[0]:
		header.append(h)

	csv_data = [header]
	for row in data:
		r = []
		for f in header:
			r.append(row[f])
		csv_data.append(r)

	return csv_data

def parse_geojson(data):
	""" Parse JSON to GEOJSON for plotting with leaflet, etc. """
	map_json = {"type": "FeatureCollection"}
	feature_list = []
	for line in data:
		d = {}
		d["type"] = "Feature"
		d["properties"] = {"ID": line['ID'],
							"Species": line['Species'],
							"X": line['geo_x'],
							"Y": line['geo_y']}
		d["geometry"] = {"type": "Point",
						"coordinates": (line['cnv_X'], line['cnv_Y'])}
		feature_list.append(d)
	for feature in feature_list:
		map_json.setdefault('features', []).append(feature)
	with open('file_geojson.geojson', 'w') as f:
		f.write(geojson.dumps(map_json))

def export_csv(data, export_file):
	""" Takes list as data and writes to .CSV file """
	with open(export_file, 'wb') as f:
		writer = csv.writer(f)
		writer.writerows(data)

def to_geo(data):
	for d in data:
		d['gcoord'] = geoconverter.GeoCoord(d['datum'], d['geo_x'], d['geo_y'])
		if d['datum'] == 'desc' or d['datum'] == 'n/a':
			d['Converts'] = 'No geo location. Value is -999'
			d['cnv_DATUM'] = d['datum']
			d['cnv_X'] = -999
			d['cnv_Y'] = -999
		if d['gcoord'].datum == "DD":
			d['Converts'] = "Do nothing, transfer coords"
			d['cnv_DATUM'] = d['datum']
			d['cnv_X'] = d['geo_x']
			d['cnv_Y'] = d['geo_y']
		elif d['gcoord'].datum == "NAD83":
			d['Converts'] = "Convert to lat long"
			coord = d['gcoord'].utm_dd()
			d['cnv_DATUM'] = coord.datum
			d['cnv_X'] = coord.x
			d['cnv_Y'] = coord.y
		elif d['gcoord'].datum == "DMS":
			d['Converts'] = "converts DMS"
			coord = d['gcoord'].dms_dd()
			d['cnv_DATUM'] = coord.datum
			d['cnv_X'] = coord.x
			d['cnv_Y'] = coord.y

	return data

def to_utm(data):
	for d in data:
		d['gcoord'] = geoconverter.GeoCoord(d['datum'], d['geo_x'], d['geo_y'])
		if d['datum'] == 'desc' or d['datum'] == 'n/a':
			d['Converts'] = 'No geo location. Value is -999'
			d['cnv_DATUM'] = d['datum']
			d['cnv_X'] = -999
			d['cnv_Y'] = -999
		if d['gcoord'].datum == "DD":
			d['Converts'] = "converts from latlong to UTM"
			coord = d['gcoord'].dd_nad83()
			d['cnv_DATUM'] = coord.datum
			d['cnv_X'] = coord.x
			d['cnv_Y'] = coord.y
		elif d['gcoord'].datum == "NAD83":
			d['Converts'] = "doesn nothing, transfers coords"
			d['cnv_DATUM'] = d['datum']
			d['cnv_X'] = d['geo_x']
			d['cnv_Y'] = d['geo_y']
		elif d['gcoord'].datum == "DMS":
			d['Converts'] = "converts DMS to DD then to UTM"
			coord = d['gcoord'].dms_dd().dd_nad83()
			d['cnv_DATUM'] = coord.datum
			d['cnv_X'] = coord.x
			d['cnv_Y'] = coord.y

	return data

def cap_species(data):
	"""Capitalizes the species name to make matching with SPECIES_DICT easier. """
	for row in data:
		row['Species'] = row['Species'].upper()
	return data

def add_speciesID(data):
	""" Adds the SpeciesID based on Species entered, can be common name or scientific name. """
	for row in data:
		species_id = [k for k, v in sp.SPECIES_DICT.iteritems() if row['Species'] in v]
		if species_id == []:
			row['SpeciesID'] = -99
		else:
			row['SpeciesID'] = species_id[0]
	return data

def in_nevada(data, datum):
	""" Checks to see if each point is in Nevada. If True, adds 1 to inNevada; else, add 0 """
	with open('NVshape.json', 'r') as f:
		nv = json.load(f)
	f.close()

	if datum == 'UTM':
		nv = nv['UTM']
	else:
		nv = nv['GEO']

	nv = mplPath.Path(nv)

	for p in data:
		if nv.contains_point([float(p['cnv_X']), float(p['cnv_Y'])]):
			p['inNevada'] = 1
		else: 
			p['inNevada'] = 0
	
	return data

#def append_species(key = speciescode, value = 'name'):

def main():
	MY_FILE = str(raw_input("Input File: "))
	f = parse_csv(MY_FILE)
	f = cap_species(f)
	f = add_speciesID(f)

	CONVERSION = raw_input("Convert To <UTM/GEO>: ")
	if CONVERSION == 'UTM':
		cnv = in_nevada(to_utm(f), 'UTM')
	elif CONVERSION == 'GEO':
		cnv = in_nevada(to_geo(f), 'GEO')

	OUT_FILE = str(raw_input("Output File: "))
	export = parse_json(cnv)
	export_csv(export, OUT_FILE)

	MAP_GEOJSON = raw_input("Export GEOJSON for mapping? <Y/N>: ")
	if MAP_GEOJSON == 'Y':
		if CONVERSION == 'UTM':
			geojson = to_geo(f)
		elif CONVERSION == 'GEO':
			geojson = cnv
		parse_geojson(geojson)

if __name__ == "__main__":
	main()