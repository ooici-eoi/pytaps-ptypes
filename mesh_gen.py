#!/usr/bin/env python

from itaps import iBase, iMesh
import utils, argparse, time


def make_2d(mesh, dims):
    print ">>>>>> make_2d"
    x,y=dims
    print "X-dim=%s, Y-dim=%s, Z-dim=%s" % (x,y,1)

    print "--> make_coords"
    t0=time.time()
    coords=utils.make_coords(x,y,1)
    print "    %.1f ms" % ((time.time()-t0)*1000)

    print "--> createVtx"
    t0=time.time()
    verts=mesh.createVtx(coords)
    print "    %.1f ms" % ((time.time()-t0)*1000)

    print "--> make_quadrilateral_vertex_array"
    t0=time.time()
#    vert_arr=utils.make_quadrilateral_vertex_array_orig(verts, x, y)
#    vert_arr=utils.make_quadrilateral_vertex_array_extend(verts, x)
    vert_arr=utils.make_quadrilateral_vertex_array(verts, x)
    print "    %.1f ms" % ((time.time()-t0)*1000)

    print "--> createEntArr quadrilaterals"
    t0=time.time()
    quads,status=mesh.createEntArr(iMesh.Topology.quadrilateral,vert_arr)
    print "    %.1f ms" % ((time.time()-t0)*1000)

    print "--> createEntSet(s)"
    set=mesh.createEntSet(ordered=False)
    set.add(quads)

    utils.print_mesh_types(mesh)

    print "<<<<<<\n"

def make_3d(mesh, dims, t3d):
    print ">>>>>> make_3d"
    x,y,z=dims
    print "X-dim=%s, Y-dim=%s, Z-dim=%s" % (x,y,z)

    print "--> make_coords"
    t0=time.time()
    coords=utils.make_coords(x,y,z)
    print "    %.1f ms" % ((time.time()-t0)*1000)

    print "--> createVtx"
    t0=time.time()
    verts=mesh.createVtx(coords)
    print "    %.1f ms" % ((time.time()-t0)*1000)

    print "--> make_hexahedron_vertex_array"
    t0=time.time()
#    vert_arr=utils.make_hexahedron_vertex_array_orig(verts, x,y,z)
#    vert_arr=utils.make_hexahedron_vertex_array_extend(verts, x,y,z)
    vert_arr=utils.make_hexahedron_vertex_array(verts, x,y,z)
    print "    %.1f ms" % ((time.time()-t0)*1000)

    print "--> createEntArr hexahedrons"
    t0=time.time()
    cubes,status=mesh.createEntArr(iMesh.Topology.hexahedron,vert_arr)
    print "    %.1f ms" % ((time.time()-t0)*1000)

    print "--> createEntSet(s)"
    if t3d:
        set=mesh.createEntSet(ordered=False)
        set.add(cubes)
    else:
        t0=time.time()
        slice_size=(x-1)*(y-1)
        # Add a set for the 'top' (5th face) of each 'layer' in the mesh
        for zi in range(z-1):
            set=mesh.createEntSet(ordered=False)
            # The 5th face (index 4) is always the top
            set.add([x[4] for x in mesh.getEntAdj(cubes[zi*slice_size:(zi+1)*slice_size], iBase.Type.face)])
        # Add a final set for the 'bottom' (6th face) of the last 'layer' in the mesh
        set=mesh.createEntSet(ordered=False)
        # The 6th face (index 5) is always the top
        set.add([x[5] for x in mesh.getEntAdj(cubes[(z-1)*slice_size:z*slice_size], iBase.Type.face)])
        print "    %.1f ms" % ((time.time()-t0)*1000)


    utils.print_mesh_types(mesh)

    print "<<<<<<\n"

parser = argparse.ArgumentParser(description='Construct a 2D, 2.5D, or 3D mesh of size <cube_dims>')
parser.add_argument('--3d', action='store_true', dest='t3d', help='If a true 3D mesh should be created.  Otherwise, creates a 2.5D mesh')
parser.add_argument('cube_dims', type=int, nargs='*', help='Integers defining the dimensions (x,y,z) of the mesh to create.  Must specify at least 2 dimensions (x,y)')
args=parser.parse_args()

dims=args.cube_dims
mesh=iMesh.Mesh()
ents=[]
if 4 > len(dims) >= 2:
    if dims[0] is 1 or dims[1] is 1:
        if dims[0] is 1 and dims[1] is 1:
            # This is a point
            print "!!> Support for points coming soon"
        else:
            # This is a line (trajectory)
            print "!!> Support for lines coming soon"

    elif len(dims) is 3:
        if dims[2] > 1:
            make_3d(mesh, dims, args.t3d)
        else:
            make_2d(mesh, dims[:-1])
    else:
        make_2d(mesh, dims)
else:
    parser.print_help()