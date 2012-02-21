#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *
import utils
import argparse

parser = argparse.ArgumentParser(description='Read amd display an imesh structured grid representation')
parser.add_argument('--c', action='store_true', dest='is_coads', help='If the coards.nc sample grid should be processed; default processes the ncom.nc sample')
parser.add_argument('--r', action='store_true', dest='is_hfr', help='If the hfr.nc sample grid should be processed; default processes the ncom.nc sample')
args=parser.parse_args()

# Setup the config for this dataset - this comes with the ExternalDataset (info provided by the registrant)
var_map={}
if args.is_coads:
    var_map['coords']={'t_var':'TIME','x_var':'COADSX','y_var':'COADSY','z_var':None}
    var_map['data']=['SST','AIRT','SPEH','WSPD','UWND','VWND','SLP']
    in_path='test_data/coads.nc'
    out_path='test_data/coads.h5m'
elif args.is_hfr:
    var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':None}
    var_map['data']=['u','v','DOPy','DOPx']
    in_path='test_data/hfr.nc'
    out_path='test_data/hfr.h5m'
else:
    var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':'depth'}
    var_map['data']=['salinity','surf_el','water_temp','water_u','water_v']
    in_path='test_data/ncom.nc'
    out_path='test_data/ncom.h5m'

# Load and process the dataset
ds=Dataset(in_path)

mesh=iMesh.Mesh()

coords_map=var_map['coords']
if coords_map['z_var']:
    zarr=ds.variables[coords_map['z_var']][:]
    z_cnt=len(zarr)

x_coords=ds.variables[coords_map['x_var']][:]
y_coords=ds.variables[coords_map['y_var']][:]
x_coords, y_coords = utils.centroid_to_vertex_coords(x_coords=x_coords, y_coords=y_coords)
x_cnt=len(x_coords)
y_cnt=len(y_coords)

coords=[]
icoords=[]
z=0
for y in range(y_cnt):
    icoords=[]
    for x in range(x_cnt):
        icoords+=[[x_coords[x],y_coords[y],z]]
    coords+=icoords
del icoords

# Create the vertices
verts=mesh.createVtx(utils.make_coords(x_cnt, y_cnt, z))
nverts=len(verts)
# Add the vertices as an EntitySet that is ordered and doesn't contain duplicates
#  Unnecessary and only complicates structure
#    vert_set=mesh.createEntSet(ordered=True)
#    vert_set.add(verts)

# Create quadrilateral entities
# Build the appropriate vertex-array from the vertices
vert_arr = utils.make_quadrilateral_vertex_array(verts=verts, x_cnt=x_cnt)

quads,status=mesh.createEntArr(iMesh.Topology.quadrilateral,vert_arr)
nquads=len(quads)

## Create Geocoordinate tag
geo_tag=mesh.createTag('GEOCOORDINATES',3,numpy.float)
geo_tag[verts]=coords

## Create tags for each data_variable
utils.make_data_tags(mesh, ds, var_map['data'], nquads)

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
if len(t_verts) == 1:
    tline_verts=[t_verts[0],t_verts[0]]
else:
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

    set.add(quads)

    for varn in var_map['data']:
        var=ds.variables[varn]
        try:
            tag=mesh.getTagHandle(utils.pack_data_tag_name(varn, var.dtype.char))
        except Exception as ex:
            print "No tag found for variable '%s'" % varn
            continue

        var.set_auto_maskandscale(False)
        if len(var.shape) == 4:
            arr=var[ti,0,:,:].reshape(nquads)
        else:
            arr=var[ti,:,:].reshape(nquads)

#        tag[set]=arr
        utils.set_packed_data(tag, set, arr)

    time_set.addChild(set)

mesh.save(out_path)
print "Saved to %s" % out_path

ds.close()

