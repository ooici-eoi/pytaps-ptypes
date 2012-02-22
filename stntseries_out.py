#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *
import utils
import argparse


parser = argparse.ArgumentParser(description='Read and display a an imesh Timeseries representation')
#parser.add_argument('--c', action='store_true', dest='is_coads', help='Process the coards.nc sample grid; otherwise process the ncom.nc sample')
parser.add_argument('--p', action='store_true', dest='do_plot', help='Plot the data for each time and variable')
args=parser.parse_args()

if True:
    in_path = 'test_data/usgs.h5m'
else:
    in_path = 'test_data/ncom.h5m'

mesh=iMesh.Mesh()
mesh.load(in_path)

t_tag=mesh.getTagHandle('TIME_DATA')
t_topo_tag=mesh.getTagHandle('TIMESTEP_TOPO')
# iBase.EntitySet returned from the tag must be 'reinitialized' as an iMesh.EntitySet
time_topo_set=iMesh.EntitySet(t_tag[mesh.rootSet],mesh)

utils.report_entset_contents(mesh, time_topo_set)

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

print "Global Attributes: %s" % gbl_atts
print "\nVariable Attributes: %s" % var_atts

print "\nGeometric Dimension: %s" % mesh.geometricDimension

tlines=time_topo_set.getEntities(topo=iMesh.Topology.line_segment)
ntimes=len(tlines)+1 # always one more timestep (vertex) than the number of line_segments
print "\n# Times: %s" % ntimes

if args.do_plot:

    # This is a timeseries - as such, we need to compile the data for each variable across all the times
    data_map={}

    ## !!!!! TWO METHODS FOR EXTRACTING DATA !!!!!
    use_method_one=False

    if use_method_one:
        ## Method one extracts data one ts at a time and builds the complete timeseries for each variable piecemeal
        # This method is slower but robust if data variables are added/removed during the timeseries
        # NOTE: does not yet deal with gaps in the timeseries
        for i in range(ntimes):
            try:
                tsvert=mesh.getEntAdj(tlines[i], iBase.Type.vertex)[0]
            except IndexError:
                tsvert=mesh.getEntAdj(tlines[i-1], iBase.Type.vertex)[0]

            topo_set=iMesh.EntitySet(t_topo_tag[tsvert],mesh)
            verts=topo_set.getEntities(type=iBase.Type.vertex)

            dtags=mesh.getAllTags(tsvert)
            for dt in (dt for dt in dtags if dt.name.startswith('DATA')):
                dtc,_=utils.unpack_data_tag_name(dt.name)
                data=utils.get_packed_data(dt, tsvert, dtc)

                if not dt.name in data_map:
                    data_map[dt.name] = data
                else:
                    data_map[dt.name] = numpy.vstack([data_map[dt.name],data])
    else:
        ## Method two extracts the entire timeseries for each variable
        # This method is faster but only works if data exists for all vertices

        # Extract the temporal vertex array from the time_topology (tlines)
        tsverts=[x[0] for x in mesh.getEntAdj(tlines,iBase.Type.vertex)]
        tsverts.append(mesh.getEntAdj(tlines[len(tlines)-1],iBase.Type.vertex)[1])
        dtags=mesh.getAllTags(tsverts[0]) # This assumes that all data_tags are present on the first vertex
        for dt in (dt for dt in dtags if dt.name.startswith('DATA')):
            dtc,_=utils.unpack_data_tag_name(dt.name)
            data=utils.get_packed_data(dt, tsverts, dtc)
            data_map[dt.name] = data


    nvars=len(data_map)
    nrow=2
    ncol=int(nvars/nrow)+1

    # Apply units, _FillValue, scale_factor, add_offset and plot
    fig = figure()
    i=1
    for var in data_map:
        dtc, varname=utils.unpack_data_tag_name(var)
        data=data_map[var]
        print "  > Plotting data for %s" % varname
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

        if not type(fill_val) in [str]:
            data=numpy.ma.masked_equal(data,fill_val,copy=False)

        # apply the scale_factor
        if scale_factor is not None:
            data=data.astype(scale_factor.dtype.char)*scale_factor
            # apply the add_offset
        if add_offset is not None:
            data+=add_offset

        a=fig.add_subplot(ncol,nrow,i)
        plot(data)
        title("%s (%s)" % (varname,units))

        i+=1

    show(0)