from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy as np
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
    var_map['data']=['water_height','water_temperature','streamflow']
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
# Set the adjacency table such that all intermediate-topologies are generated
mesh.adjTable = np.array([[7, 4, 4, 1],[1, 7, 5, 5],[1, 5, 7, 5],[1, 5, 5, 7]], dtype='int32')

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

#stn_loc=mesh.createVtx([0,0,0]) # Geocoordinate stored in a field
stn_loc=mesh.createVtx(coord) # Geocoordinates stored in mesh
ntopo=1

# Create the Topology set
topo_set=mesh.createEntSet(False)
topo_set.add(stn_loc)

### Create Geocoordinate tag -- When Geocoordinates are stored in a field
#geo_tag=mesh.createTag('GEOCOORDINATES',3,numpy.float)
#geo_tag[stn_loc]=coord

## Create tags for each data_variable
utils.make_data_tags(mesh, ds, var_map['data'], ntopo)

## Add variable attribute tags
utils.make_var_attr_tags(mesh, ds)

## Add global attribute tags
utils.make_gbl_attr_tags(mesh, ds)

# Build the time information
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
ttopo_tag=mesh.createTag('TIMESTEP_TOPO',1,iMesh.EntitySet)

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

    # Process each variable
    for varn in var_map['data']:
        var=ds.variables[varn]
        try:
            tag=mesh.getTagHandle(utils.pack_data_tag_name(varn, var.dtype.char))
        except Exception as ex:
            print "No tag found for variable '%s'" % varn
            continue

        var.set_auto_maskandscale(False)

        arr=var[ti].reshape(ntopo)

        utils.set_packed_data(tag, tsvert, arr)
#        tag[tsvert]=arr


mesh.save(out_path)
print "Saved to %s" % out_path

ds.close()