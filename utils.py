#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
import numpy as np

def print_mesh_types(mesh):
    print "Mesh [%s]:" \
          "\n\t%d EntitySets" \
          "\n\t%d vertices" \
          "\n\t%d faces" \
          "\n\t%d edges" \
          "\n\t%d regions" % (mesh,
                              len(mesh.getEntSets()),
                              mesh.getNumOfType(iBase.Type.vertex),
                              mesh.getNumOfType(iBase.Type.face),
                              mesh.getNumOfType(iBase.Type.edge),
                              mesh.getNumOfType(iBase.Type.region))

from itertools import *

def iterblocks(iterable, size, blocktype=list):
    iterator = iter(iterable)
    while True:
        block = blocktype(islice(iterator,size))
        if not block:
            break

        yield block

def make_coords(x_cnt, y_cnt, z_cnt):
    if z_cnt > 1:
        coords=[[x,y,z] for z in xrange(z_cnt) for y in xrange(y_cnt) for x in xrange(x_cnt)]
    else:
        coords=[[x,y,0] for y in xrange(y_cnt) for x in xrange(x_cnt)]

    return coords

def make_quadrilateral_vertex_array(verts, x_cnt):
    vert_arr=[]
    for x in (x for x in xrange(len(verts)-x_cnt-1) if (x+1) % x_cnt != 0):
        vert_arr.append(verts[x])
        vert_arr.append(verts[x+1])
        vert_arr.append(verts[x+1+x_cnt])
        vert_arr.append(verts[x+x_cnt])

    return vert_arr

def make_quadrilateral_vertex_array_extend(verts, x_cnt):
    vert_arr=[]
    for x in (x for x in xrange(len(verts)-x_cnt-1) if (x+1) % x_cnt != 0):
        vert_arr.extend(verts[x:x+2])
        vert_arr.extend(verts[x+1+x_cnt:x+x_cnt-1:-1])

    return vert_arr

def make_quadrilateral_vertex_array_old(verts, x_cnt, y_cnt):
    vert_arr=[]
    for y in range(y_cnt-1):
        for x in range(x_cnt-1):
            xi=x+x_cnt*y

            a=xi
            b=xi+1
            c=(((y+1)*x_cnt+xi)+1)-(x_cnt*y)
            d=(((y+1)*x_cnt+xi))-(x_cnt*y)
#            print a,b,c,d

            try:
                vert_arr+=[verts[a],verts[b],verts[c],verts[d]]
            except IndexError as ie:
                raise ie

    return vert_arr

def make_hexahedron_vertex_array(verts, x_cnt, y_cnt, z_cnt):
    vert_arr=[]
    zii=0
    for z in range(z_cnt-1):
        zi=(x_cnt*y_cnt)*(z+1)
        for x in (x for x in xrange((len(verts)/z_cnt)-x_cnt-1) if (x+1) % x_cnt != 0):
            vert_arr.append(verts[x+zii])
            vert_arr.append(verts[x+1+zii])
            vert_arr.append(verts[x+1+x_cnt+zii])
            vert_arr.append(verts[x+x_cnt+zii])

            vert_arr.append(verts[x+zi])
            vert_arr.append(verts[x+1+zi])
            vert_arr.append(verts[x+1+x_cnt+zi])
            vert_arr.append(verts[x+x_cnt+zi])

        zii=zi

    return vert_arr

def make_hexahedron_vertex_array_extend(verts, x_cnt, y_cnt, z_cnt):
    vert_arr=[]
    zii=0
    for z in range(z_cnt-1):
        zi=(x_cnt*y_cnt)*(z+1)
        for x in (x for x in xrange((len(verts)/z_cnt)-x_cnt-1) if (x+1) % x_cnt != 0):
            vert_arr.extend(verts[x+zii:x+2+zii])
            vert_arr.extend(verts[x+1+x_cnt+zii:x+x_cnt-1+zii:-1])
            vert_arr.extend(verts[x+zi:x+zi+2])
            vert_arr.extend(verts[x+1+x_cnt+zi:x+x_cnt-1+zi:-1])

        zii=zi

    return vert_arr

def make_hexahedron_vertex_array_old(verts, x_cnt, y_cnt, z_cnt):
    vert_arr=[]
    zii=0
    for z in range(z_cnt-1):
        zi=(x_cnt*y_cnt)*(z+1)
#        print zi
        for y in range(y_cnt-1):
            for x in range(x_cnt-1):
                xi=x+x_cnt*y

                a=xi
                b=xi+1
                c=(((y+1)*x_cnt+xi)+1)-(x_cnt*y)
                d=(((y+1)*x_cnt+xi))-(x_cnt*y)

                e=a+zi
                f=b+zi
                g=c+zi
                h=d+zi

                a+=zii
                b+=zii
                c+=zii
                d+=zii

#                print a,b,c,d,e,f,g,h

                try:
                    vert_arr+=[verts[a],verts[b],verts[c],verts[d],
                               verts[e],verts[f],verts[g],verts[h]]
                except IndexError as ie:
                    raise ie
        zii=zi

    return vert_arr

def extend_uniform_array(arr):
    darr=arr[1:]-arr[:-1]
    if darr.std() > 1e-5:
        raise Exception("Cannot extend non-uniform array")
    dx=darr.mean()
    arr-=(dx*0.5)
    arr=np.append(arr,[arr[-1]+dx])
    return arr

def centroid_to_vertex_coords(x_coords, y_coords):
    return extend_uniform_array(x_coords), extend_uniform_array(y_coords)

def process_attribute(mesh, attr_name, attr_val):
    if type(attr_val) in [unicode, str]:
        dtype=np.byte
        arr=np.fromstring(attr_val,dtype=dtype)
    else:
        dtype=np.typeDict[attr_val.dtype.char]
        if dtype == np.int16:
            dtype = np.int32
        elif dtype == np.float32:
            dtype = np.float64
        arr=attr_val

    mesh.createTag(attr_name,arr.size,dtype)[mesh.rootSet]=arr

def report_entset_contents(mesh, entity_set, indent=""):
    print indent+"EntitySet [%s]{" % entity_set

    # Check for types in this entity_set
    if entity_set.getNumOfType(iBase.Type.all) != 0:
        if entity_set.getNumOfType(iBase.Type.edge) > 0:
            print indent+" # edges: %s" % entity_set.getNumOfType(iBase.Type.edge)
        if entity_set.getNumOfType(iBase.Type.face) > 0:
            print indent+" # faces: %s" % entity_set.getNumOfType(iBase.Type.face)
        if entity_set.getNumOfType(iBase.Type.region) > 0:
            print indent+" # regions: %s" % entity_set.getNumOfType(iBase.Type.region)
        if entity_set.getNumOfType(iBase.Type.vertex) > 0:
            print indent+" # vertices: %s" % entity_set.getNumOfType(iBase.Type.vertex)

    # Check for topologies in this entity_set
    if entity_set.getNumOfTopo(iMesh.Topology.all) != 0:
        if entity_set.getNumOfTopo(iMesh.Topology.hexahedron) > 0:
            print indent+" # hexahedrons: %s" % entity_set.getNumOfTopo(iMesh.Topology.hexahedron)
        if entity_set.getNumOfTopo(iMesh.Topology.line_segment) > 0:
            print indent+" # line_segments: %s" % entity_set.getNumOfTopo(iMesh.Topology.line_segment)
        if entity_set.getNumOfTopo(iMesh.Topology.point) > 0:
            print indent+" # points: %s" % entity_set.getNumOfTopo(iMesh.Topology.point)
        if entity_set.getNumOfTopo(iMesh.Topology.polygon) > 0:
            print indent+" # polygons: %s" % entity_set.getNumOfTopo(iMesh.Topology.polygon)
        if entity_set.getNumOfTopo(iMesh.Topology.polyhedron) > 0:
            print indent+" # polyhedrons: %s" % entity_set.getNumOfTopo(iMesh.Topology.polyhedron)
        if entity_set.getNumOfTopo(iMesh.Topology.prism) > 0:
            print indent+" # prisms: %s" % entity_set.getNumOfTopo(iMesh.Topology.prism)
        if entity_set.getNumOfTopo(iMesh.Topology.pyramid) > 0:
            print indent+" # pyramids: %s" % entity_set.getNumOfTopo(iMesh.Topology.pyramid)
        if entity_set.getNumOfTopo(iMesh.Topology.quadrilateral) > 0:
            print indent+" # quadrilaterals: %s" % entity_set.getNumOfTopo(iMesh.Topology.quadrilateral)
        if entity_set.getNumOfTopo(iMesh.Topology.septahedron) > 0:
            print indent+" # septahedrons: %s" % entity_set.getNumOfTopo(iMesh.Topology.septahedron)
        if entity_set.getNumOfTopo(iMesh.Topology.tetrahedron) > 0:
            print indent+" # tetrahedrons: %s" % entity_set.getNumOfTopo(iMesh.Topology.tetrahedron)
        if entity_set.getNumOfTopo(iMesh.Topology.triangle) > 0:
            print indent+" # triangles: %s" % entity_set.getNumOfTopo(iMesh.Topology.triangle)

    tags=mesh.getAllTags(entity_set)
    print indent+" # tags: %s" % len(tags)


    if entity_set.getNumEntSets() != 0:
        for es in entity_set.getEntSets():
            report_entset_contents(mesh, es, indent=indent+"   ")

    if entity_set.getNumChildren() != 0:
        for ch in entity_set.getChildren():
            if type(ch) is iMesh.EntitySet:
                report_entset_contents(mesh, ch, indent=indent+"   ")

    print indent+"}"

def set_packed_data(tag, key, value):
    tag[key] = np.frombuffer(np.asarray(value), dtype=np.byte)

def get_packed_data(tag, key, dtype):
    return np.frombuffer(tag[key], dtype=dtype)

def pack_data_tag_name(varname, dtype_char):
    return 'DATA_%s_%s' % (dtype_char, varname)

def unpack_data_tag_name(data_tag_name):
    varname=data_tag_name.replace('DATA_','')
    return varname.split('_', 1)

def make_data_tags(mesh, ds, data_vars, data_dim):
    ## Create tags for each data_variable
    for varn in data_vars:
        var=ds.variables[varn]
        dt=var.dtype
        ## By using the packing methods above, all tags can be made as the byte type
        mesh.createTag(pack_data_tag_name(varn, dt.char), (data_dim*dt.itemsize), np.byte)

def make_var_attr_tags(mesh, ds):
    for varn in ds.variables:
        var=ds.variables[varn]
        for attn in var.ncattrs():
            process_attribute(mesh, "VAR_ATT_%s::%s" % (varn, attn), var.getncattr(attn))

def make_gbl_attr_tags(mesh, ds):
    for gattn in ds.ncattrs():
        process_attribute(mesh, "GBL_ATT_"+gattn, ds.getncattr(gattn))
