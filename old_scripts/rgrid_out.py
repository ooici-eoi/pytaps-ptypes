#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *

def report_entset_contents(entity_set, indent=""):
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
            report_entset_contents(es, indent=indent+"   ")

    print indent+"}"

import argparse
parser = argparse.ArgumentParser(description='Process a structured grid to an imesh representation')
parser.add_argument('--c', action='store_true', dest='is_coads', help='If the coards.nc sample grid should be processed; otherwise process the ncom.nc sample')
args=parser.parse_args()

if args.is_coads:
    in_path = 'test_data/coads.h5m'
else:
    in_path = 'test_data/ncom.h5m'

mesh=iMesh.Mesh()
mesh.load(in_path)

ent_sets=mesh.getEntSets()
for es in ent_sets:
    report_entset_contents(es)

# Get global and variable attributes
var_atts={}
gbl_atts={}
tags=mesh.getAllTags(mesh.rootSet)
for t in tags:
    val = t[mesh.rootSet]
    if val.dtype == numpy.int8:
        val = val.tostring()

    #    print "%s : %s" % (t.name, val)

    if t.name.startswith('GBL_ATT_'):
        gbl_atts[t.name.replace('GBL_ATT_','')]=val
    elif t.name.startswith('VAR_ATT_'):
        vn,an=t.name.replace('VAR_ATT_','').split('::',1)
        if vn not in var_atts:
            var_atts[vn]={}
        var_atts[vn][an]=val

#print "Global Attributes: %s" % gbl_atts
#print "\nVariable Attributes: %s" % var_atts


# We know this is a rectilinear grid, which means we know there are quadrilateral entities,
# so get them, get the data tags associated with them, and then loop through them to plot the data
quads=mesh.getEntities(topo=iMesh.Topology.quadrilateral)
fig=figure()
from matplotlib import cm
from matplotlib.collections import PolyCollection

# Find all the data tags
dtags=mesh.getAllTags(quads[0])
ntags=len(dtags)
nrow=2
ncol=int(ntags/nrow)+1
for i in range(ntags):
    data_t=dtags[i]
    print "> Plotting data for %s" % data_t.name
    varname=data_t.name.replace('DATA_','')
    # Get the units, _FillValue, scale_factor, and add_offset
    fill_val=numpy.nan
    scale_factor=None
    add_offset=None
    units='Unknown'
    if varname in var_atts:
        if '_FillValue' in var_atts[varname]:
            fill_val=var_atts[varname]['_FillValue']
        if 'scale_factor' in var_atts[varname]:
            scale_factor=var_atts[varname]['scale_factor']
        if 'add_offset' in var_atts[varname]:
            add_offset=var_atts[varname]['add_offset']
        if 'units' in var_atts[varname]:
            units=var_atts[varname]['units']

    data=data_t[quads]
    data=numpy.ma.masked_equal(data,fill_val,copy=False)
    # apply the scale_factor
    if scale_factor is not None:
        data=data.astype(numpy.float64)*scale_factor
        # apply the add_offset
    if add_offset is not None:
        data+=add_offset

    qvert_list=mesh.getEntAdj(quads,iBase.Type.vertex)
    poly_list=[]
    for qv in qvert_list:
        cds=mesh.getVtxCoords(qv)
        poly_list.append(cds[:,[0,1]].tolist())

    pcoll=PolyCollection(poly_list, edgecolor='none')
    pcoll.set_array(data)
    pcoll.set_cmap(cm.jet)

    a=fig.add_subplot(ncol,nrow,i+1)
    a.add_collection(pcoll, autolim=True)
    a.autoscale_view()
    colorbar(pcoll,orientation='vertical')
    title("%s (%s)" % (varname,units))


show(0)
