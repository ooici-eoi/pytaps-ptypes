#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
import numpy

def make_quadrilateral_vertex_array(verts, x_cnt, y_cnt):
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

def centroid_to_vertex_coords(x_coords, y_coords):
    #    x_cnt=len(x_coords)
    #    print "original x_cnt: %s" % x_cnt
    dxarr=(x_coords[1:]-x_coords[0:-1])
    if dxarr.std() != 0.0:
        raise Exception("Non-uniform x array")
    dx=dxarr.mean()
    #    print "delta_x: %f" % dx
    #    print "Shift the x array by -delta_x/2 and add 1 value to the end of the array == x_coords[-1]+delta_x"
    x_coords-=(dx*0.5)
    x_coords=numpy.append(x_coords,[x_coords[-1]+dx])
    #    x_cnt=len(x_coords)
    #    print "new x_cnt: %s" % x_cnt

    #    y_cnt=len(y_coords)
    #    print "original y_cnt: %s" % y_cnt
    dyarr=(y_coords[1:]-y_coords[0:-1])
    if dyarr.std() != 0.0:
        raise Exception("Non-uniform y array")
    dy=dyarr.mean()
    #    print "delta_y: %f" % dx
    #    print "Shift the y array by -delta_y/2 and add 1 value to the end of the array == y_coords[-1]+delta_y"
    y_coords-=(dy*0.5)
    y_coords=numpy.append(y_coords,[y_coords[-1]+dy])
    #    y_cnt=len(y_coords)
    #    print "new y_cnt: %s" % y_cnt

    return x_coords, y_coords

def process_attribute(mesh, attr_name, attr_val):
    if type(attr_val) in [unicode, str]:
        dtype=numpy.byte
        arr=numpy.fromstring(attr_val,dtype=dtype)
    else:
        dtype=numpy.typeDict[attr_val.dtype.char]
        if dtype == numpy.int16:
            dtype = numpy.int32
        elif dtype == numpy.float32:
            dtype = numpy.float64
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
    tag[key] = numpy.frombuffer(numpy.asarray(value), dtype=numpy.byte)

def get_packed_data(tag, key, dtype):
    return numpy.frombuffer(tag[key], dtype=dtype)

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
        mesh.createTag(pack_data_tag_name(varn, dt.char), (data_dim*dt.itemsize), numpy.byte)

def make_var_attr_tags(mesh, ds):
    for varn in ds.variables:
        var=ds.variables[varn]
        for attn in var.ncattrs():
            process_attribute(mesh, "VAR_ATT_%s::%s" % (varn, attn), var.getncattr(attn))

def make_gbl_attr_tags(mesh, ds):
    for gattn in ds.ncattrs():
        process_attribute(mesh, "GBL_ATT_"+gattn, ds.getncattr(gattn))
