print('Importing Libraries')
from astroplan import Observer, FixedTarget
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
from datetime import datetime
import pandas as pd
from geopy.geocoders import GoogleV3
from bokeh.io import  output_file, show
from bokeh.layouts import widgetbox, column
from bokeh.models.widgets import Paragraph, Select, Div
from bokeh.models import ColumnDataSource
from bokeh.models.callbacks import CustomJS
from bokeh.embed import components
from tqdm import tqdm

print('Setting up')
def az_to_coord(az):
    if (337.5 <= az) or (az <= 22.5):
        return 'North'
    elif (az <= 67.5):
        return 'North-East'
    elif (az <= 112.5):
        return 'East'
    elif (az <= 157.5):
        return 'South-East'
    elif (az <= 202.5):
        return 'South'
    elif (az <= 247.5):
        return 'South-West'
    elif (az < 292.5):
        return 'West'
    else:
        return 'North-West'

RA_Kepler = 320.40*u.deg
DEC_Kepler = -15.74*u.deg
coord = SkyCoord(ra=RA_Kepler, dec=DEC_Kepler)
Kepler = FixedTarget(coord=coord, name='Kepler')

g = GoogleV3()

t_start = datetime(2017, 12, 10, 21, 38) #in UTC
t_end = datetime(2017, 12, 10, 22, 8)
cities = pd.read_csv('simplemaps-worldcities-basic.csv')
cities = cities[cities['pop'] > 1000000].reset_index()
cities['name'] = cities['city_ascii'] + ', ' + cities['iso3']
alts = []
azs = []
messages = []

print('Calculating')
for row in tqdm(cities.itertuples(), total=len(cities)):
    lat, lon = row.lat, row.lng
    obs = Observer(location=EarthLocation.from_geodetic(lon*u.deg, lat*u.deg))
    altaz = obs.altaz(t_start, Kepler)
    alt = altaz.alt.deg
    az = altaz.az.deg
    direc = az_to_coord(az)
    tz = g.timezone((lat, lon))
    t0 = tz.fromutc(t_start)
    t1 = tz.fromutc(t_end)
    alts.append(alt)
    azs.append(az)
    if alt < 0.:
        message = 'Kepler will be to the %s,'%(direc) + '<p>' +'%.0f degrees below the horizon'%(-alt)
    else:
        message = 'Kepler will be to the %s,'%(direc) + '<p>' + '%.0f degrees above the horizon'%(alt)
    message += '<br>The image will be taken between %02d:%02d and %02d:%02d local time on December %dth'%(t0.hour, t0.minute, t1.hour, t1.minute, t1.day)
    message += '<br>We hope you\'ll join us in waving to Kepler!'
    messages.append([message])

print('Saving Results')
cities['message'] = messages

results = ColumnDataSource(cities.set_index('name').to_dict()['message'])

args = dict(results=results)
update = CustomJS(args=args, code="""
   par.text = results.data[select.value][0];
""")

p = Div(text=results.data['New York, USA'][0], width=400, height=100)
select = Select(title='Nearest City:', value='New York, USA', options=sorted(cities['name'].values), callback=update)
update.args['par'] = p
update.args['select'] = select
layout = column([select, p])
script, div = components(layout)

name1 = 'web_app.script'
name2 = 'web_app.div'

print('Saving results as components: %s and %s'%(name1, name2))
with open(name1, 'w') as f:
    f.write(script)
    f.write('\n')
    
with open(name2, 'w') as f:
    f.write(div)
    f.write('\n')

print('Launching Website')
show(layout)
