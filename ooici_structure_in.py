#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *
import utils
import argparse


def pack_data_tag_name(varname, dtype_char, cell_dim=0):
    return 'DATA_%s_%s_%s' % (cell_dim, dtype_char, varname)

def make_data_tags(mesh, ds, data_vars, data_dim, cell_dim=0):
    ## Create tags for each data_variable
    for varn in data_vars:
        var=ds.variables[varn]
        dt=var.dtype

        dpth=1
        shp=var.shape
        #        if len(shp) is 4:
        #            dsize=data_dim*shp[1]*dt.itemsize
        #        else:
        #            dsize=data_dim*dt.itemsize
        dsize=data_dim*dt.itemsize
        ## By using the packing methods above, all tags can be made as the byte type
        mesh.createTag(pack_data_tag_name(varn, dt.char, cell_dim), dsize, np.byte)



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
    var_map['2_data']=['salinity','surf_el','water_temp','water_u','water_v']
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

z=0
coords=[[x_coords[x],y_coords[y],z] for y in xrange(y_cnt) for x in xrange(x_cnt)]

# Create the vertices
#verts=mesh.createVtx(utils.make_coords(x_cnt, y_cnt, z)) # Geocoordinate stored in a field
verts=mesh.createVtx(coords) # Geocoordinates stored in mesh

# Create quadrilateral entities
# Build the appropriate vertex-array from the vertices
vert_arr = utils.make_quadrilateral_vertex_array(verts=verts, x_cnt=x_cnt)

quads,status=mesh.createEntArr(iMesh.Topology.quadrilateral,vert_arr)
ntopo=len(quads)

# Create the Topology set
topo_set=mesh.createEntSet(False)
topo_set.add(quads)
for edges in mesh.getEntAdj(quads,type=1):
    topo_set.add(edges)
topo_set.add(verts)
#topo_set.add(mesh.getEntAdj(quads,type=1))
#topo_set.add(mesh.getEntAdj(quads,type=0))

### Create Geocoordinate tag -- When Geocoordinates are stored in a field
#geo_tag=mesh.createTag('GEOCOORDINATES',3,numpy.float)
#geo_tag[verts]=coords

## Create tags for each data_variable
# NOTE: THIS ASSUMES ALL DATA ON FACES (true for ncom)
make_data_tags(mesh, ds, var_map['2_data'], ntopo, 2)

### Add variable attribute tags
#utils.make_var_attr_tags(mesh, ds)
#
### Add global attribute tags
#utils.make_gbl_attr_tags(mesh, ds)

tvarn=coords_map['t_var']
tvar=ds.variables[tvarn]
ntimes=tvar.size

tarr=tvar[:]
tcoords=[]
for t in xrange(ntimes):
    tcoords+=[[tarr[t],0,0]]

t_verts=mesh.createVtx(tcoords)

tline_verts=[]
if len(t_verts) == 1:
    tline_verts=[t_verts[0],t_verts[0]]
else:
    for t in xrange(len(t_verts)-1):
        tline_verts+=[t_verts[t],t_verts[t+1]]

tline,status=mesh.createEntArr(iMesh.Topology.line_segment,tline_verts)
time_topo_set=mesh.createEntSet(False)
time_topo_set.add(tline)
time_topo_set.add(t_verts)

# Create a time_topology tag
ttopo_tag=mesh.createTag('TIMESTEP_TOPO',1,iMesh.EntitySet)
ttopo_tag[time_topo_set]=topo_set

# Create a time_set to contain the topo and data sets
#time_set=mesh.createEntSet(ordered=False)

# Create a time_tag to reference the temporal information
time_tag=mesh.createTag('TIME_DATA',1,iMesh.EntitySet)
time_tag[mesh.rootSet] = time_topo_set

# Process each timestep
for ti in xrange(ntimes):
    # Get the vertex for this timestep
    tsvert=t_verts[ti]

#    # Reference the topology for this timestep
#    ttopo_tag[tsvert]=topo_set

    for varn in var_map['2_data']:
        var=ds.variables[varn]
        try:
            tag=mesh.getTagHandle(pack_data_tag_name(varn, var.dtype.char, 2))
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

# Delete the 'default' tags that we don't need/want
mesh.destroyTag(mesh.getTagHandle('DIRICHLET_SET'), True)
mesh.destroyTag(mesh.getTagHandle('GEOM_DIMENSION'), True)
mesh.destroyTag(mesh.getTagHandle('GLOBAL_ID'), True)
mesh.destroyTag(mesh.getTagHandle('MATERIAL_SET'), True)
mesh.destroyTag(mesh.getTagHandle('NEUMANN_SET'), True)

mesh.save(out_path)
print "Saved to %s" % out_path

ds.close()

