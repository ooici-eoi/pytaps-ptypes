#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
import numpy
from numpy.random import uniform, randint
from pylab import *


mesh=iMesh.Mesh()

coords=[]
icoords=[]
z=0

x_cnt=15
y_cnt=9
for y in range(y_cnt):
    icoords=[]
    for x in range(x_cnt):
        icoords+=[[x,y,z]]
    coords+=icoords
del icoords
print len(coords)

# Create the vertices
verts=mesh.createVtx(coords)
# Add the vertices as an EntitySet that is ordered and doesn't contain duplicates
vert_set=mesh.createEntSet(ordered=True)
vert_set.add(verts)

# Create quadrilateral entities
# Build the appropriate vertex-array from the vertices
vert_arr=[]
edge_arr=[]
nverts=len(verts)
for y in range(y_cnt-1):
    for x in range(x_cnt-1):
        xi=x+x_cnt*y

        a=xi
        b=xi+1
        c=(((y+1)*x_cnt+xi)+1)-(x_cnt*y)
        d=(((y+1)*x_cnt+xi))-(x_cnt*y)
        print a,b,c,d
        try:
            vert_arr+=[verts[a],verts[b],verts[c],verts[d]]
        except IndexError as ie:
            print ie
            break

quads,status=mesh.createEntArr(iMesh.Topology.quadrilateral,vert_arr)#, create_if_missing=True)
# Add the quads as an EntitySet that is unordered and may contain duplicates
quad_set=mesh.createEntSet(ordered=False)
quad_set.add(quads)

#edges,status=mesh.createEntArr(iMesh.Topology.line_segment,edge_arr)
#edge_set=mesh.createEntSet(ordered=False)
#edge_set.add(edges)

print "%d vertices, %d faces, %d edges" % (mesh.getNumOfType(iBase.Type.vertex),
                                           mesh.getNumOfType(iBase.Type.face),
                                           mesh.getNumOfType(iBase.Type.edge))

# Assign some data

# To the mesh itself
strb=numpy.fromstring("String value for tag", numpy.byte)
bm_tag=mesh.createTag("byte_mesh_data",len(strb),numpy.byte)
bm_tag[mesh]=strb

# To the quadrilateral faces
ff_dat=uniform(10,25,len(quads))
ff_tag=mesh.createTag("float_face_data",1,numpy.float64)
ff_tag[quads]=ff_dat

if_dat=randint(50,80,len(quads)).astype('int32')
if_tag=mesh.createTag("int_face_data",1,numpy.int32)
if_tag[quads]=if_dat

# To the vertices
fv_dat=uniform(10,25,len(verts))
fv_tag=mesh.createTag("float_vertex_data",1,numpy.float64)
fv_tag[verts]=fv_dat

# To the EntitySet
qs_tag=mesh.createTag("int_quads_tag",1,numpy.int32)
qs_tag[quad_set]=111

vs_tag=mesh.createTag("int_verts_tag",1,numpy.int32)
vs_tag[vert_set]=222

out_path = "out.h5m"

mesh.save(out_path)

print "Saved to %s" % out_path