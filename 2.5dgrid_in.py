#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *
import utils
import argparse
import time

parser = argparse.ArgumentParser(description='Process a structured grid to an imesh representation')
parser.add_argument('--c', action='store_true', dest='is_coads', help='If the coards.nc sample grid should be processed; otherwise process the ncom.nc sample')
args=parser.parse_args()

# Setup the config for this dataset - this comes with the ExternalDataset (info provided by the registrant)
var_map={}
if args.is_coads:
    var_map['coords']={'t_var':'TIME','x_var':'COADSX','y_var':'COADSY','z_var':None}
    var_map['data']=['SST','AIRT','SPEH','WSPD','UWND','VWND','SLP']
    in_path='test_data/coads.nc'
    out_path='test_data/coads.h5m'
else:
    var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':'depth'}
    var_map['data']=['salinity','surf_el','water_temp','water_u','water_v']
    in_path='test_data/ncom.nc'
    out_path='test_data/ncom2.5d.h5m'

# Load and process the dataset
ds=Dataset(in_path)

mesh=iMesh.Mesh()

coords_map=var_map['coords']
z_cnt=1
if coords_map['z_var']:
    z_coords=ds.variables[coords_map['z_var']][:]
    z_cnt=len(z_coords)

x_coords=ds.variables[coords_map['x_var']][:]
y_coords=ds.variables[coords_map['y_var']][:]
x_coords, y_coords = utils.centroid_to_vertex_coords(x_coords=x_coords, y_coords=y_coords)
x_cnt=len(x_coords)
y_cnt=len(y_coords)

coords=[]
for z in range(z_cnt):
    for y in range(y_cnt):
        for x in range(x_cnt):
            coords+=[[x_coords[x],y_coords[y],z_coords[z]]]

# Create the vertices
verts=mesh.createVtx(coords)
nverts=len(verts)

# Build the appropriate vertex-array from the vertices
vert_arr = utils.make_hexahedron_vertex_array(verts=verts, x_cnt=x_cnt, y_cnt=y_cnt, z_cnt=z_cnt)

cubes,status=mesh.createEntArr(iMesh.Topology.hexahedron,vert_arr)
nquads=len(cubes)
slice_size=(x_cnt-1)*(y_cnt-1)
# Add a set for the 'top' (5th face) of each 'layer' in the mesh
for zi in range(z_cnt-1):
    set=mesh.createEntSet(ordered=False)
    # The 5th face (index 4) is always the top
    set.add([x[4] for x in mesh.getEntAdj(cubes[zi*slice_size:(zi+1)*slice_size], iBase.Type.face)])
    # Add a final set for the 'bottom' (6th face) of the last 'layer' in the mesh
set=mesh.createEntSet(ordered=False)
# The 6th face (index 5) is always the top
set.add([x[5] for x in mesh.getEntAdj(cubes[(z_cnt-1)*slice_size:z_cnt*slice_size], iBase.Type.face)])

## Create tags for each data_variable
utils.make_data_tags(mesh, ds, var_map['data'], nquads)

### Add variable attribute tags
#utils.make_var_attr_tags(mesh, ds)
#
### Add global attribute tags
#utils.make_gbl_attr_tags(mesh, ds)

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

### Note:  ITAPS entity sets can be either ordered or unordered.
### Ordered sets, as the name implies, store their contents in sorted order and do not store duplicates.
### Unordered sets store their contents in the order they were added and do store duplicates.
#
## Create a time_set to add child timesteps into
#time_set=mesh.createEntSet(ordered=False)
#
## Add the time_set to the TIME_DATA tag
#time_tag[mesh.rootSet]=time_set
#
#for ti in range(ntimes):
#    set=mesh.createEntSet(ordered=False)
#
#    set.add(quads)
#
#    for varn in var_map['data']:
#        var=ds.variables[varn]
#        try:
#            tag=mesh.getTagHandle(utils.pack_data_tag_name(varn, var.dtype.char))
#        except Exception as ex:
#            print "No tag found for variable '%s'" % varn
#            continue
#
#        var.set_auto_maskandscale(False)
#        if len(var.shape) == 4:
#            arr=var[ti,0,:,:].reshape(nquads)
#        else:
#            arr=var[ti,:,:].reshape(nquads)
#
##        tag[set]=arr
#        utils.set_packed_data(tag, set, arr)
#
#    time_set.addChild(set)

#mesh.optimize()

#mesh.save(out_path)
#print "Saved to %s" % out_path
#
#ds.close()

