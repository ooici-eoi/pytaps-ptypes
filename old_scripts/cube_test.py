#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
import utils
import argparse


def print_mesh(mesh):
    print "Mesh [%s]:  %d vertices, %d faces, %d edges, %d regions" % (mesh,
                                                                       mesh.getNumOfType(iBase.Type.vertex),
                                                                       mesh.getNumOfType(iBase.Type.face),
                                                                       mesh.getNumOfType(iBase.Type.edge),
                                                                       mesh.getNumOfType(iBase.Type.region))

def make_coords(x_cnt, y_cnt, z_cnt):
    coords=[]
    for z in range(z_cnt):
        for y in range(y_cnt):
            for x in range(x_cnt):
                coords+=[[x,y,z]]

    return coords

parser = argparse.ArgumentParser(description='Construct a 3D mesh of size <num_cubes>')
parser.add_argument('num_cubes', type=int, nargs='*', default=1, help='The number of cubes to create (1, 2, etc)')
args=parser.parse_args()

for num in args.num_cubes:
    print ">>>>>>"
    mesh=iMesh.Mesh()

    fail=False

    if num == 1:
        print "X-dim=%s, Y-dim=%s, Z-dim=%s" % (2,2,2)
        coords=make_coords(2,2,2)
#        coords=[[0,0,0], #0
#            [1,0,0], #1
#            [0,1,0], #2
#            [1,1,0], #3
#            [0,0,1], #4
#            [1,0,1], #5
#            [0,1,1], #6
#            [1,1,1]] #7


        # Create the vertices
        verts=mesh.createVtx(coords)

        vert_arr=utils.make_hexahedron_vertex_array(verts, 2, 2, 2)

#        # Build the appropriate vertex-array from the vertices
#        vert_arr=[verts[0],verts[1],verts[3],verts[2],verts[4],verts[5],verts[7],verts[6]]
    elif num == 2:
        print "X-dim=%s, Y-dim=%s, Z-dim=%s" % (3,2,2)
        coords=make_coords(3,2,2)
#        coords=[[0,0,0],
#            [1,0,0],
#            [2,0,0],
#            [0,1,0],
#            [1,1,0],
#            [2,1,0],
#            [0,0,1],
#            [1,0,1],
#            [2,0,1],
#            [0,1,1],
#            [1,1,1],
#            [2,1,1]]

        # Create the vertices
        verts=mesh.createVtx(coords)

        vert_arr=utils.make_hexahedron_vertex_array(verts, 3, 2, 2)

#        # Build the appropriate vertex-array from the vertices
#        vert_arr=[]
#        vert_arr+=[verts[0],verts[1],verts[4],verts[3],verts[6],verts[7],verts[10],verts[9]]
#        vert_arr+=[verts[1],verts[2],verts[5],verts[4],verts[7],verts[8],verts[11],verts[10]]
    elif num == 3:
        print "X-dim=%s, Y-dim=%s, Z-dim=%s" % (4,2,2)
        coords=make_coords(4,2,2)
#        coords=[[0,0,0],
#            [1,0,0],
#            [2,0,0],
#            [3,0,0],
#            [0,1,0],
#            [1,1,0],
#            [2,1,0],
#            [3,1,0],
#            [0,0,1],
#            [1,0,1],
#            [2,0,1],
#            [3,0,1],
#            [0,1,1],
#            [1,1,1],
#            [2,1,1],
#            [3,1,1]]

        # Create the vertices
        verts=mesh.createVtx(coords)

        vert_arr=utils.make_hexahedron_vertex_array(verts, 4, 2, 2)

#        # Build the appropriate vertex-array from the vertices
#        vert_arr=[]
#        vert_arr+=[verts[0],verts[1],verts[5],verts[4],verts[8],verts[9],verts[13],verts[12]]
#        vert_arr+=[verts[1],verts[2],verts[6],verts[5],verts[9],verts[10],verts[14],verts[13]]
#        vert_arr+=[verts[2],verts[3],verts[7],verts[6],verts[10],verts[11],verts[15],verts[14]]
    elif num == 4:
        print "X-dim=%s, Y-dim=%s, Z-dim=%s" % (3,3,2)
        coords=make_coords(3,3,2)
#        coords=[[0,0,0],
#            [1,0,0],
#            [2,0,0],
#            [0,1,0],
#            [1,1,0],
#            [2,1,0],
#            [0,2,0],
#            [1,2,0],
#            [2,2,0],
#            [0,0,1],
#            [1,0,1],
#            [2,0,1],
#            [0,1,1],
#            [1,1,1],
#            [2,1,1],
#            [0,2,1],
#            [1,2,1],
#            [2,2,1]]

        # Create the vertices
        verts=mesh.createVtx(coords)

        vert_arr=utils.make_hexahedron_vertex_array(verts, 3, 3, 2)

#        # Build the appropriate vertex-array from the vertices
#        vert_arr=[]
#        vert_arr+=[verts[0],verts[1],verts[4],verts[3],verts[9],verts[10],verts[13],verts[12]]
#        vert_arr+=[verts[1],verts[2],verts[5],verts[4],verts[10],verts[11],verts[14],verts[13]]
#        vert_arr+=[verts[3],verts[4],verts[7],verts[6],verts[12],verts[13],verts[16],verts[15]]
#        vert_arr+=[verts[4],verts[5],verts[8],verts[7],verts[13],verts[14],verts[17],verts[16]]
    else:
        print "num_cubes %s is not supported" % num
        fail=True

    if not fail:
        print "--> hexahedrons"
        cube,status=mesh.createEntArr(iMesh.Topology.hexahedron,vert_arr)
        print_mesh(mesh)

    print "<<<<<<\n"