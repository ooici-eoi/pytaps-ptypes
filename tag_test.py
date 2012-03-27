#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
import numpy as np

mesh=iMesh.Mesh()
# Set the adjacency table such that all intermediate-topologies are generated
mesh.adjTable = np.array([[7, 4, 4, 1],[1, 7, 5, 5],[1, 5, 7, 5],[1, 5, 5, 7]], dtype='int32')

# Delete the 'default' tags that we don't need/want
mesh.destroyTag(mesh.getTagHandle('DIRICHLET_SET'), True)
mesh.destroyTag(mesh.getTagHandle('GEOM_DIMENSION'), True)
mesh.destroyTag(mesh.getTagHandle('GLOBAL_ID'), True)
mesh.destroyTag(mesh.getTagHandle('MATERIAL_SET'), True)
mesh.destroyTag(mesh.getTagHandle('NEUMANN_SET'), True)


coords=[]
for x in xrange(10):
    coords+=[[x,0,0]]

#mesh.geometricDimension=1
#coords=np.array(np.arange(10)).astype(np.int32).reshape(10,1)

verts=mesh.createVtx(coords)
vert_set=mesh.createEntSet(False)
vert_set.add(verts)

everts=[]
for x in range(len(verts)-1):
    everts+=[verts[x],verts[x+1]]
    
# Create edges
edges, status = mesh.createEntArr(iMesh.Topology.line_segment, everts)

# Make vertex data
vdata=np.arange(10).astype(np.int32)
# Make multi-dim data (arrays on verts)
mdata=np.empty([10,10]).astype(np.int32)
for x in xrange(10):
    mdata[x]=vdata.copy()
# Make edge data
edata=np.arange(100,109).astype(np.int32)

# tag values on vertex enties
ents_tag=mesh.createTag('values_on_verts', 1, np.int32)
ents_tag[verts]=vdata

# tag arrays on vertices
mv_ents_tag=mesh.createTag('multi_value_on_verts', vdata.size, np.int32)
mv_ents_tag[verts]=mdata

# tag data on entity set
eset_tag=mesh.createTag('values_on_vert_ent_set', vdata.size, np.int32)
eset_tag[vert_set]=vdata

# tag first and last vertex values
fl_tag=mesh.createTag('values_on_first_last_verts', 1, np.int32)
fl_tag[verts[0]] = vdata[0]
fl_tag[verts[-1]] = vdata[-1]


a_tag=mesh.createTag('tag_a', 1, np.int32)
# tag all vertices
a_tag[verts] = vdata
# tag the first and last edges
a_tag[edges[0]] = edata[0]
a_tag[edges[-1]] = edata[-1]

b_tag=mesh.createTag('tag_b', 1, np.int32)
# tag the first and last vertices
b_tag[verts[0]] = vdata[0]
b_tag[verts[-1]] = vdata[-1]
# tag all edges
b_tag[edges] = edata

mesh.save('tag_test.h5m')