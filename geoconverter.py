import math

def geo_constants(datum):
	if datum == "NAD83":
		E = 0.00669438
		R = 6378137
	elif datum == "NAD27":
		E = 0.006768658
		R = 6378206.4

	K0 = 0.9996

	E2 = E * E
	E3 = E2 * E
	E_P2 = E / (1.0 - E)

	SQRT_E = math.sqrt(1 - E)
	_E = (1 - SQRT_E) / (1 + SQRT_E)
	_E2 = _E * _E
	_E3 = _E2 * _E
	_E4 = _E3 * _E
	_E5 = _E4 * _E

	M1 = (1 - E / 4 - 3 * E2 / 64 - 5 * E3 / 256)
	M2 = (3 * E / 8 + 3 * E2 / 32 + 45 * E3 / 1024)
	M3 = (15 * E2 / 256 + 45 * E3 / 1024)
	M4 = (35 * E3 / 3072)

	P2 = (3. / 2 * _E - 27. / 32 * _E3 + 269. / 512 * _E5)
	P3 = (21. / 16 * _E2 - 55. / 32 * _E4)
	P4 = (151. / 96 * _E3 - 417. / 128 * _E5)
	P5 = (1097. / 512 * _E4)

	return {'K0': K0, 'E': E, 'E2': E2, 'E3': E3, 'E_P2': E_P2, 'SQRT_E': SQRT_E, '_E': _E,
			'_E2': _E2, '_E3': _E3, '_E4': _E4, '_E5': _E5, 'M1': M1, 'M2': M2, 'M3': M3,
			'M4': M4, 'P2':P2, 'P3': P3, 'P4':P4, 'P5':P5, 'R':R}

def convert_dms(degrees, minutes, seconds):
	""" Converts degrees minutes seconds into decimal degrees. """
	return int(degrees) + (int(minutes) * (1/60.)) + (int(seconds) * (1/3600.)) 

class GeoCoord(object):
	""" GeoCoord class for Geographic Coordinates. 
		datum = ['NAD83', 'NAD27', 'DD', 'DMS']
		if DMS format must be 'ddd mm ss'
		zonenumber and zoneletter required for UTM only """
	def __init__(self, datum, x, y):
		self.datum = datum
		self.x = x
		self.y = y

	def __str__(self):
		return "datum: %r, x: %r, y: %r" % (self.datum, self.x, self.y)

	def dms_dd(self):
		""" Converts DMS to DD give DMS was formatted with spaces"""
		# TODO if Degrees is negative return proper coords, only difference is - sign
		x = self.x.split()
		y = self.y.split()

		x_deg = abs(float(x[0]))
		x_min = float(x[1])
		x_sec = float(x[2])
		y_deg = float(y[0])
		y_min = float(y[1])
		y_sec = float(y[2])

		x_dd = convert_dms(x_deg, x_min, x_sec)
		y_dd = convert_dms(y_deg, y_min, y_sec)

		return GeoCoord("DD", -x_dd, y_dd)

	def dd_nad83(self):
		""" Convert DD to NAD83 
			self.x must be negative (western hemisphere)"""
		x = float(self.x)
		y = float(self.y)
		C = geo_constants("NAD83")

		zone_number = 11

		lat_rad = math.radians(y)
		lat_sin = math.sin(lat_rad)
		lat_cos = math.cos(lat_rad)
		lat_tan = lat_sin / lat_cos
		lat_tan2 = lat_tan * lat_tan
		lat_tan4 = lat_tan2 * lat_tan2

		lon_rad = math.radians(x)
		central_lon = -117 #only because this is for Zone 11 only
		central_lon_rad = math.radians(central_lon)

		n = C['R'] / math.sqrt(1 - C['E'] * lat_sin**2)
		c = C['E_P2'] * lat_cos**2

		a = lat_cos * (lon_rad - central_lon_rad)
		a2 = a * a
		a3 = a2 * a
		a4 = a3 * a
		a5 = a4 * a
		a6 = a5 * a

		m = C['R'] * (C['M1'] * lat_rad -
			C['M2'] * math.sin(2 * lat_rad) +
			C['M3'] * math.sin(4 * lat_rad) - 
			C['M4'] * math.sin(6 * lat_rad))

		easting = C['K0'] * n * (a +
							a3 / 6 * (1 - lat_tan2 +  c) +
							a5 / 120 * (5 - 18 * lat_tan2 + lat_tan4 + 72 * c - 58 * C['E_P2'])) + 500000

		northing = C['K0'] * (m + n * lat_tan * (a2 / 2 +
											a4 / 24 * (5 - lat_tan2 + 9 * c + 4 * c**2) +
											a6 / 720 * (61 - 58 * lat_tan2 + lat_tan4 + 600 * c - 330 * C['E_P2'])))
		return GeoCoord("NAD83", easting, northing)

	def utm_dd(self):
		""" Converts UTM to Geopgraphic, datum is used to generate 
			Ellipsoid shape, eccentiricity. """
		C = geo_constants(self.datum)

		x = float(self.x) - 500000
		y = float(self.y)

		m = y / C['K0']
		mu = m / (C['R'] * C['M1'])

		p_rad = (mu +
				C['P2'] * math.sin(2 * mu) +
				C['P3'] * math.sin(4 * mu) +
				C['P4'] * math.sin(6 * mu) +
				C['P5'] * math.sin(8 * mu))
		p_sin = math.sin(p_rad)
		p_sin2 = p_sin * p_sin
		p_cos = math.cos(p_rad)
		p_tan = p_sin / p_cos
		p_tan2 = p_tan * p_tan
		p_tan4 = p_tan2 * p_tan2

		ep_sin = 1 - C['E'] * p_sin2
		ep_sin_sqrt = math.sqrt(1 - C['E'] * p_sin2)

		n = C['R'] / ep_sin_sqrt
		r = (1 - C['E']) / ep_sin
		c = C['_E'] * p_cos**2
		c2 = c * c

		d = x / (n * C['K0'])
		d2 = d * d
		d3 = d2 * d
		d4 = d3 * d
		d5 = d4 * d
		d6 = d5 * d

		latitude = (p_rad - (p_tan / r) *
					(d2 / 2 -
					d4 / 24 * (5 + 3 * p_tan2 + 10 * c - 4 * c2 - 9 * C['E_P2'])) +
					d6 / 720 * (61 + 90 * p_tan2 + 298 * c + 45 * p_tan4 - 252 * C['E_P2'] - 3 * c2))

		longitude = (d -
					d3 / 6 * (1 + 2 * p_tan2 + c) +
					d5 / 120 * (5 - 2 * c + 28 * p_tan2 - 3 * c2 + 8 * C['E_P2'] + 24 * p_tan4)) / p_cos

		latitude = math.degrees(latitude)
		longitude = math.degrees(longitude) + -117
		return GeoCoord("DD", longitude, latitude)

	def change_projection(self):
		""" When converting from NAD27 to NAD83 use this to convert Geo coord to WGS84/NAD83 """
		x = math.radians(self.x)
		y = math.radians(self.y)

		a = 6378206.4
		f = 1.0 / 294.9786982
		dx = -8
		dy = 160
		dz = 176
		da = 6378137 - a 
		df = (1.0 / 298.257223563) - f

		x_sin = math.sin(x)
		x_cos = math.cos(x)
		y_sin = math.sin(y)
		y_sin2 = y_sin * y_sin
		y_cos = math.cos(y)

		e2 = f*(2-f)

		rho = a * (1 - e2) / (1 - e2 * y_sin2) ** 1.5
		nu = a / (1 - e2 * y_sin) ** 0.5

		geoy = (1/rho) * (-dx * y_sin * x_cos - dy * y_sin * x_sin + dz * y_cos + (f * da + a * df) * math.sin(2*y))
		geox = (-dx * x_sin + dy * x_cos) / (nu * y_cos)

		nx = math.degrees(x + geox)
		ny = math.degrees(y + geoy)

		return GeoCoord("DD", nx, ny)