#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *


# Load the ncom dataset
ds=Dataset('test_data/ncom.nc')
# Setup the config for this dataset - this comes with the ExternalDataset (info provided by the registrant)
out_path = "test_data/ncom.h5m"
var_map={}
var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':'depth'}
var_map['data']=['salinity','surf_el','water_temp','water_u','water_v']

mesh=iMesh.Mesh()

coords_map=var_map['coords']
if coords_map['z_var']:
    zarr=ds.variables[coords_map['z_var']][:]
    z_cnt=len(zarr)

x_coords=ds.variables[coords_map['x_var']][0:14]
y_coords=ds.variables[coords_map['y_var']][0:8]
x_cnt=len(x_coords)
#    print "original x_cnt: %s" % x_cnt
dxarr=(x_coords[1:]-x_coords[0:-1])
if dxarr.std() != 0.0:
    raise Exception("Non-uniform x array")
dx=dxarr.mean()
#    print "delta_x: %f" % dx
#    print "Shift the x array by -delta_x/2 and add 1 value to the end of the array == x_coords[-1]+delta_x"
x_coords-=(dx*0.5)
x_coords=numpy.append(x_coords,[x_coords[-1]+dx])
x_cnt=len(x_coords)
#    print "new x_cnt: %s" % x_cnt

y_cnt=len(y_coords)
#    print "original y_cnt: %s" % y_cnt
dyarr=(y_coords[1:]-y_coords[0:-1])
if dyarr.std() != 0.0:
    raise Exception("Non-uniform y array")
dy=dyarr.mean()
#    print "delta_y: %f" % dx
#    print "Shift the y array by -delta_y/2 and add 1 value to the end of the array == y_coords[-1]+delta_y"
y_coords-=(dy*0.5)
y_coords=numpy.append(y_coords,[y_coords[-1]+dy])
y_cnt=len(y_coords)
#    print "new y_cnt: %s" % y_cnt

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
verts=mesh.createVtx(coords)
nverts=len(verts)
# Add the vertices as an EntitySet that is ordered and doesn't contain duplicates
vert_set=mesh.createEntSet(ordered=True)
vert_set.add(verts)

# Create quadrilateral entities
# Build the appropriate vertex-array from the vertices
vert_arr=[]
for y in range(y_cnt-1):
    for x in range(x_cnt-1):
        xi=x+x_cnt*y
#        yi=y*y_cnt

        a=xi
        b=xi+1
        c=(((y+1)*x_cnt+xi)+1)-(x_cnt*y)
        d=(((y+1)*x_cnt+xi))-(x_cnt*y)
#        print a,b,c,d
        try:
            vert_arr+=[verts[a],verts[b],verts[c],verts[d]]
        except IndexError as ie:
            raise ie

quads,status=mesh.createEntArr(iMesh.Topology.quadrilateral,vert_arr)
# Add the quads as an EntitySet that is unordered and may contain duplicates
quad_set=mesh.createEntSet(ordered=False)
quad_set.add(quads)
nquads=len(quads)

print "%d vertices, %d faces, %d edges" % (mesh.getNumOfType(iBase.Type.vertex),
                                           mesh.getNumOfType(iBase.Type.face),
                                           mesh.getNumOfType(iBase.Type.edge))

## Assign the dataset data
#for varn in var_map['data']:
#    var=ds.variables[varn]
#    var.set_auto_maskandscale(False)
#    type=var.dtype
#    tag=None
#    if type in [numpy.byte,numpy.int8,numpy.int16,numpy.int32,numpy.float32,numpy.float64]:
#        if len(var.shape) == 4:
#            arr=var[0,0,:,:].reshape(nquads)
#        else:
#            arr=var[0,:,:].reshape(nquads)
#
#        if type == numpy.int16:
#            tag=mesh.createTag('DATA_'+varn,1,numpy.int32)
#            tag[quads]=arr.astype(numpy.int32)
#        elif type == numpy.float32:
#            tag=mesh.createTag('DATA_'+varn,1,numpy.float64)
#            tag[quads]=arr.astype(numpy.float64)
#        else:
#            tag=mesh.createTag('DATA_'+varn,1,type)
#            tag[quads]=arr
#    else:
#        raise Exception("Type %s not supported" % type)
#
##    if tag:
##        # add var attribute tags to the data tag
##        for attn in var.ncattrs():
##            att=var.getncattr(attn)
##            strarr=numpy.fromstring(att,dtype=numpy.byte)
##            mesh.createTag("VAR_ATT_%s_%s" % (varn,attn),strarr.size,numpy.byte)[verts[0]]=strarr
#
## Global Attributes
##for gattn in ds.ncattrs():
##    gatt=ds.getncattr(gattn)
##    strarr=numpy.fromstring(gatt,dtype=numpy.byte)
##    mesh.createTag('GBL_ATT_'+gattn,strarr.size,numpy.byte)[verts[0]]=strarr
#
#mesh.save(out_path)
#print "Saved to %s" % out_path


