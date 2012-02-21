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
    out_path='test_data/v_coads.h5m'
elif args.is_hfr:
    var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':None}
    var_map['data']=['u','v','DOPy','DOPx']
    in_path='test_data/hfr.nc'
    out_path='test_data/v_hfr.h5m'
else:
    var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':'depth'}
    var_map['data']=['salinity','surf_el','water_temp','water_u','water_v']
    in_path='test_data/ncom.nc'
    out_path='test_data/v_ncom.h5m'

# Load and process the dataset
ds=Dataset(in_path)

mesh=iMesh.Mesh()

coords_map=var_map['coords']
if coords_map['z_var']:
    zarr=ds.variables[coords_map['z_var']][:]
    z_cnt=len(zarr)

x_coords=ds.variables[coords_map['x_var']][:]
y_coords=ds.variables[coords_map['y_var']][:]
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
#verts=mesh.createVtx(utils.make_coords(x_cnt, y_cnt, z)) # Geocoordinate stored in a field
verts=mesh.createVtx(coords) # Geocoordinates stored in mesh
ntopo=len(verts)

# Create the Topology set
topo_set=mesh.createEntSet(False)
topo_set.add(verts)

### Create Geocoordinate tag -- When Geocoordinates are stored in a field
#geo_tag=mesh.createTag('GEOCOORDINATES',3,numpy.float)
#geo_tag[verts]=coords

## Create tags for each data_variable
utils.make_data_tags(mesh, ds, var_map['data'], ntopo)

## Add variable attribute tags
utils.make_var_attr_tags(mesh, ds)

## Add global attribute tags
utils.make_gbl_attr_tags(mesh, ds)

tvarn=coords_map['t_var']
tvar=ds.variables[tvarn]
ntimes=tvar.size

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
time_topo_set=mesh.createEntSet(False)
time_topo_set.add(tline)

# Create a time_topology tag
ttopo_tag=mesh.createTag('TIMESTEP_TOPO',1,iBase.EntitySet)

# Create a time_set to contain the topo and data sets
time_set=mesh.createEntSet(ordered=False)

# Create a time_tag to reference the temporal information
time_tag=mesh.createTag('TIME_DATA',1,iMesh.EntitySet)
time_tag[mesh.rootSet] = time_topo_set

# Process each timestep
for ti in range(ntimes):
    # Get the vertex for this timestep
    tsvert=t_verts[ti]

    # Reference the topology for this timestep
    ttopo_tag[tsvert]=topo_set

    for varn in var_map['data']:
        var=ds.variables[varn]
        try:
            tag=mesh.getTagHandle(utils.pack_data_tag_name(varn, var.dtype.char))
        except Exception as ex:
            print "No tag found for variable '%s'" % varn
            continue

        var.set_auto_maskandscale(False)
        if len(var.shape) == 4:
            arr=var[ti,0,:,:].reshape(ntopo)
        else:
            arr=var[ti,:,:].reshape(ntopo)

        utils.set_packed_data(tag, tsvert, arr)
#        tag[set]=arr

mesh.save(out_path)
print "Saved to %s" % out_path

ds.close()

