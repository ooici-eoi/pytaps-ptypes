from itaps import iBase, iMesh, iGeom, iRel
import utils

# Make & save the first mesh
m1=iMesh.Mesh()

coords1=[[x,0,0] for x in xrange(10)]

m1verts=m1.createVtx(coords1)

m1line_verts=[]
for x in xrange(len(m1verts)-1):
    m1line_verts+=[m1verts[x],m1verts[x+1]]

m1line, status=m1.createEntArr(iMesh.Topology.line_segment, m1line_verts)

m1set=m1.createEntSet(False)
m1set.add(m1line)

#m1tag=m1.createTag('m1_tag',1,int)
m1tag=m1.createTag('tag',1,int)
m1tag[m1set]=1

m1.save('m1.h5m')

# Make & save the second mesh
m2=iMesh.Mesh()

coords2=[[x,0,0] for x in xrange(11)]
m2verts=m2.createVtx(coords2)

m2line_verts=[]
for x in xrange(len(m2verts)-1):
    m2line_verts+=[m2verts[x],m2verts[x+1]]

m2line, status=m2.createEntArr(iMesh.Topology.line_segment, m2line_verts)

m2set=m2.createEntSet(False)
m2set.add(m2line)

#m2tag=m2.createTag('m2_tag',1,int)
m2tag=m2.createTag('tag',1,int)
m2tag[m2set]=2

m2.save('m2.h5m')

rel=iRel.Rel()
rel.createPair(m1,iRel.Type.set,iRel.Status.active,m1,iRel.Type.set,iRel.Status.active)

# Read both into 1 mesh
mcomb=iMesh.Mesh()
mcomb.load('m1.h5m')
mcomb.load('m2.h5m')