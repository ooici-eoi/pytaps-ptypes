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

# Load and process the dataset
ds=Dataset(in_path)

# Create the 'master' mesh
m_mesh=iMesh.Mesh()
# Set the adjacency table such that all intermediate-topologies are generated
mesh.adjTable = np.array([[7, 4, 4, 1],[1, 7, 5, 5],[1, 5, 7, 5],[1, 5, 5, 7]], dtype='int32')

# Build the time information
coords_map=var_map['coords']
tvar=ds.variables[coords_map['t_var']]
ntimes=tvar.size

# Get the time data and make time coordinates (using i index of coordinate tuple i,j,k)
tarr=tvar[:]
tcoords=[]
for t in range(ntimes):
    tcoords+=[[tarr[t],0,0]]

# Create time vertex entities
t_verts=m_mesh.createVtx(tcoords)

# Arrange the vertices to build the temporal topology
tline_verts=[]
if ntimes == 1:
    tline_verts=[t_verts[0],t_verts[0]]
else:
    for t in range(len(t_verts)-1):
        tline_verts+=[t_verts[t],t_verts[t+1]]

# Create the temporal topology
tline,status=m_mesh.createEntArr(iMesh.Topology.line_segment,tline_verts)
temporal_set=m_mesh.createEntSet(False)
temporal_set.add(tline)

# Arbitrarily break the timeseries into 'ranges' (for testing purposes)
breaks=[5,20,40,55,80,102,ntimes-1]
trange_verts=[]
if ntimes == 1:
    trange_verts=[t_verts[0],t_verts[0]]
else:
    s=0
    for i in breaks:
        trange_verts+=[t_verts[s],t_verts[i]]
        s=i

# Create the tRange topology
tranges,status=m_mesh.createEntArr(iMesh.Topology.line_segment,trange_verts)

#arr=numpy.empty([0,1])
#for x in m_mesh.getEntAdj(tranges, iBase.Type.vertex):
#    arr = numpy.vstack([arr,m_mesh.getVtxCoords(x)[:,[0]]])

# Now start processing data

#for rng in tranges:
#    vts=m_mesh.getEntAdj(rng, iBase.Type.vertex)
#    si=t_verts.index(vts[0])
#    ei=t_verts.index(vts[1])
#    print si, ei