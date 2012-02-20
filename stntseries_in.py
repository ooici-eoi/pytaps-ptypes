from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *
import utils
import argparse

parser = argparse.ArgumentParser(description='Process a Timeseries to an imesh representation')
#parser.add_argument('--a', action='store_true', dest='is_ast2', help='If the ast2.nc sample grid should be processed; otherwise process the ncom.nc sample')
args=parser.parse_args()

# Setup the config for this dataset - this comes with the ExternalDataset (info provided by the registrant)
var_map={}
if True:
    var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':'z'}
    var_map['data']=['water_height','data_qualifier','water_temperature','streamflow','water_height_datum']
    in_path='test_data/usgs.nc'
    out_path='test_data/usgs.h5m'
else:
    var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':'depth'}
    var_map['data']=['salinity','surf_el','water_temp','water_u','water_v']
    in_path='test_data/ncom.nc'
    out_path='test_data/ncom.h5m'

# Load and process the dataset
ds=Dataset(in_path)

mesh=iMesh.Mesh()

coords_map=var_map['coords']
z_cnt = 0
if coords_map['z_var']:
    zarr=ds.variables[coords_map['z_var']][:]
    z_cnt=len(zarr)

x_coords=ds.variables[coords_map['x_var']][:]
y_coords=ds.variables[coords_map['y_var']][:]
x_cnt=len(x_coords)
y_cnt=len(y_coords)

if x_cnt != 1 or y_cnt != 1:
    raise Exception("A station timeseries must have exactly 1 set of x/y coordinates, is this a Trajectory?")

z_crd=0
if z_cnt > 0:
    z_crd=zarr[0]

coord = [x_coords[0],y_coords[0],z_crd]

stn_loc=mesh.createVtx([0,0,0])

## Create Geocoordinate tag
geo_tag=mesh.createTag('GEOCOORDINATES',3,numpy.float)
geo_tag[stn_loc]=coord

## Create tags for each data_variable
utils.make_data_tags(mesh, ds, var_map['data'], 1)

## Add variable attribute tags
utils.make_var_attr_tags(mesh, ds)

## Add global attribute tags
utils.make_gbl_attr_tags(mesh, ds)

tvarn=coords_map['t_var']
tvar=ds.variables[tvarn]
ntimes=tvar.size
time_tag=mesh.createTag('TIME_DATA',1,iMesh.EntitySet)
tarr=tvar[:]
tcoords=[]
for t in range(ntimes):
    tcoords+=[[tarr[t],0,0]]

t_verts=mesh.createVtx(tcoords)

tline_verts=[]
for t in range(len(t_verts)-1):
    tline_verts+=[t_verts[t],t_verts[t+1]]

tline,status=mesh.createEntArr(iMesh.Topology.line_segment,tline_verts)

## Note:  ITAPS entity sets can be either ordered or unordered.
## Ordered sets, as the name implies, store their contents in sorted order and do not store duplicates.
## Unordered sets store their contents in the order they were added and do store duplicates.

# Create a time_set to add child timesteps into
time_set=mesh.createEntSet(ordered=False)

# Add the time_set to the TIME_DATA tag
time_tag[mesh.rootSet]=time_set

for ti in range(ntimes):
    set=mesh.createEntSet(ordered=False)

    set.add(stn_loc)

    for varn in var_map['data']:
        var=ds.variables[varn]
        try:
            tag=mesh.getTagHandle(utils.pack_data_tag_name(varn, var.dtype.char))
        except Exception as ex:
            print "No tag found for variable '%s'" % varn
            continue

        var.set_auto_maskandscale(False)

        arr=var[ti].reshape(1)

        utils.set_packed_data(tag, set, arr)
#        tag[set]=arr

    time_set.addChild(set)

mesh.save(out_path)
print "Saved to %s" % out_path

ds.close()