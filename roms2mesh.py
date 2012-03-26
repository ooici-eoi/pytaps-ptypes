#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *
import utils
import argparse


def pack_data_tag_name(varname, dtype_char, cell_dim='s0'):
    return 'DATA_%s_%s_%s' % (cell_dim, dtype_char, varname)

def make_data_tags(mesh, ds, data_vars, data_dim, cell_dim='s0'):
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

in_path='test_data/roms.nc'
out_path='test_data/roms.h5m'
coords_map={'t_var':'ocean_time', 'x_var':'lon_psi', 'y_var':'lat_psi'}
var_map={}
# TODO: NOTE: These are NOT paying attention to level right now
var_map['S0']=['shflux','swrad','zeta','salt','temp','AKs','AKt','AKv', 'w']
var_map['S1Y']=['DU_avg1','DU_avg2','sustr','ubar','u']
var_map['S1X']=['DV_avg1','DV_avg2','svstr','vbar','v']

# Load and process the dataset
ds=Dataset(in_path)

mesh=iMesh.Mesh()

x_coords=ds.variables[coords_map['x_var']][:]
x_shp=x_coords.shape
x_coords=x_coords.flatten()
y_coords=ds.variables[coords_map['y_var']][:]
y_shp=y_coords.shape
y_coords=y_coords.flatten()
#x_coords, y_coords = utils.centroid_to_vertex_coords(x_coords=x_coords, y_coords=y_coords)
x_cnt=x_shp[0]
y_cnt=x_shp[1]

z=0
z_coords=np.zeros(len(x_coords))

coords=np.column_stack([x_coords,y_coords,z_coords])
#coords=[[x_coords[x],y_coords[y],z] for y in xrange(y_cnt) for x in xrange(x_cnt)]

# Create the vertices
#verts=mesh.createVtx(utils.make_coords(x_cnt, y_cnt, z)) # Geocoordinate stored in a field
verts=mesh.createVtx(coords) # Geocoordinates stored in mesh
s0_set=mesh.createEntSet(True)
s0_set.add(verts)
s0_len=len(verts)
s0_tag=mesh.createTag('S0', 1, iMesh.EntitySet)
s0_tag[mesh.rootSet]=s0_set

## Create quadrilateral entities
## Build the appropriate vertex-array from the vertices
vert_arr = utils.make_quadrilateral_vertex_array(verts=verts, x_cnt=x_cnt)

quads,status=mesh.createEntArr(iMesh.Topology.quadrilateral,vert_arr)

# Create the entity_set of dimension-2
s2_set=mesh.createEntSet(True)
s2_set.add(quads)
s2_len=len(quads)
s2_tag=mesh.createTag('S2', 1, iMesh.EntitySet)
s2_tag[mesh.rootSet]=s2_set

# Pull out the 'x_edges' and 'y_edges'
qedges=mesh.getEntAdj(quads,type=1)
x_edges=[]
y_edges=[]
for e in qedges:
    #TODO: Must use lists because the equality check is borked with numpy1.6, so can't use np.unique
    if not e[3] in y_edges:
        y_edges.append(e[3])
    if not e[1] in y_edges:
        y_edges.append(e[1])
    if not e[0] in x_edges:
        x_edges.append(e[0])
    if not e[2] in x_edges:
        x_edges.append(e[2])

# Reorder the edges from the first row of faces - they're in "bottom, top" order by cell
xpop=x_edges[1:(x_cnt*2-1)]
rep=xpop[1::2]
rep.extend(xpop[0::2])
x_edges[1:(x_cnt*2-1)]=rep

# Create a tag & entity_set for the x_edges
s1x_set=mesh.createEntSet(True)
s1x_set.add(x_edges)
s1x_len=len(x_edges)
s1x_tag=mesh.createTag('S1X', 1, iMesh.EntitySet)
s1x_tag[mesh.rootSet]=s1x_set

# Create a tag & entity_set for the y_edges
s1y_set=mesh.createEntSet(True)
s1y_set.add(y_edges)
s1y_len=len(y_edges)
s1y_tag=mesh.createTag('S1Y', 1, iMesh.EntitySet)
s1y_tag[mesh.rootSet]=s1y_set


#### Create Geocoordinate tag -- When Geocoordinates are stored in a field
##geo_tag=mesh.createTag('GEOCOORDINATES',3,numpy.float)
##geo_tag[verts]=coords
#
## Create tags for each data_variable
make_data_tags(mesh, ds, var_map['S0'], s0_len, 'S0')
make_data_tags(mesh, ds, var_map['S1X'], s1x_len, 'S1X')
make_data_tags(mesh, ds, var_map['S1Y'], s1y_len, 'S1Y')

#### Add variable attribute tags
##utils.make_var_attr_tags(mesh, ds)
##
#### Add global attribute tags
##utils.make_gbl_attr_tags(mesh, ds)

tvarn=coords_map['t_var']
tvar=ds.variables[tvarn]
ntimes=tvar.size

tarr=tvar[:]
tcoords=[]
for t in xrange(ntimes):
    tcoords+=[[tarr[t],0,0]]

t_verts=mesh.createVtx(tcoords)
t0_set=mesh.createEntSet(True)
t0_set.add(t_verts)
t0_tag=mesh.createTag('T0',1,iMesh.EntitySet)
t0_tag[mesh.rootSet] = t0_set

tline_verts=[]
if len(t_verts) == 1:
    tline_verts=[t_verts[0],t_verts[0]]
else:
    for t in xrange(len(t_verts)-1):
        tline_verts+=[t_verts[t],t_verts[t+1]]

tline,status=mesh.createEntArr(iMesh.Topology.line_segment,tline_verts)
t1_set=mesh.createEntSet(True)
t1_set.add(tline)
t1_tag=mesh.createTag('T1',1,iMesh.EntitySet)
t1_tag[mesh.rootSet] = t1_set

## Process each timestep
for ti in xrange(ntimes):
    print '>>> Proc TS: {0}'.format(ti)
    # Get the vertex for this timestep
    tsvert=t_verts[ti]

#    # Reference the topology for this timestep
#    ttopo_tag[tsvert]=s2_set

    for topo_key in var_map:
        topo_len=len(utils.getEntitiesByTag(mesh, topo_key))
        print '\t{0}: {1}'.format(topo_key, topo_len)
        for varn in var_map[topo_key]:
            var=ds.variables[varn]
            print '\t\t{0}: {1}'.format(varn, var.shape)
            try:
                tag=mesh.getTagHandle(pack_data_tag_name(varn, var.dtype.char, topo_key))
            except Exception as ex:
                print "No tag found for variable '%s'" % varn
                continue

            var.set_auto_maskandscale(False)
            if len(var.shape) == 4:
                arr=var[ti,0,1:,1:].reshape(topo_len)
            else:
                arr=var[ti,1:,1:].reshape(topo_len)


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

#ds.close()