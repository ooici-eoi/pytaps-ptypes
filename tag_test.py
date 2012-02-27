#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
import numpy as np

mesh=iMesh.Mesh()
coords=[]
for x in xrange(10):
    coords+=[[x,0,0]]

#mesh.geometricDimension=1
#coords=np.array(np.arange(10)).astype(np.int32).reshape(10,1)

verts=mesh.createVtx(coords)
vert_set=mesh.createEntSet(False)
vert_set.add(verts)

data=np.arange(10).astype(np.int32)
mdata=np.empty([10,10]).astype(np.int32)
for x in xrange(10):
    mdata[x]=data.copy()

ents_tag=mesh.createTag('values_on_ents', 1, np.int32)
ents_tag[verts]=data

mv_ents_tag=mesh.createTag('multi_value_on_ents', data.size, np.int32)
mv_ents_tag[verts]=mdata

eset_tag=mesh.createTag('values_on_ent_set', data.size, np.int32)
eset_tag[vert_set]=data

fl_tag=mesh.createTag('values_on_first_last_ents', 1, np.int32)
fl_tag[verts[0]] = data[0]
fl_tag[verts[-1]] = data[-1]


mesh.save('tag_test.h5m')