#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from matplotlib import cm
import numpy
from pylab import *
import utils
import argparse


parser = argparse.ArgumentParser(description='Process a structured grid to an imesh representation')
parser.add_argument('--c', action='store_true', dest='is_coads', help='Process the coards.nc sample grid; otherwise process the ncom.nc sample')
parser.add_argument('--r', action='store_true', dest='is_hfr', help='Process the hfr.nc sample grid; otherwise process the ncom.nc sample')
parser.add_argument('--p', action='store_true', dest='do_plot', help='Plot the data for each time and variable')
parser.add_argument('time_indices', metavar='N', type=int, nargs='*',
    help='comma separated list of the temporal indices to plot; if empty, plot all times')
args=parser.parse_args()

if args.is_coads:
    in_path = 'test_data/v_coads.h5m'
elif args.is_hfr:
    in_path = 'test_data/v_hfr.h5m'
else:
    in_path = 'test_data/v_ncom.h5m'
    md_shp=[34,57,89]

mesh=iMesh.Mesh()
mesh.load(in_path)

t_tag=mesh.getTagHandle('TIME_DATA')
t_topo_tag=mesh.getTagHandle('TIMESTEP_TOPO')
# iBase.EntitySet returned from the tag must be 'reinitialized' as an iMesh.EntitySet
time_topo_set=iMesh.EntitySet(t_tag[mesh.rootSet],mesh)

#t_set=mesh.getEntSets()[0]
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
    if len(args.time_indices) == 0:
        args.time_indices = range(ntimes)

    print "Plot time indices: %s" % args.time_indices

    for i in args.time_indices:
        if i >= ntimes:
            print "Cannot Plot: Index %s is outside the bounds of the time array (max is %s)" % (i, ntimes-1)
            continue
        print "Plotting data for time index %s" % i
        try:
            tsvert=mesh.getEntAdj(tlines[i], iBase.Type.vertex)[0]
        except IndexError:
            tsvert=mesh.getEntAdj(tlines[i-1], iBase.Type.vertex)[0]

        fig=figure()
#        fig.suptitle="Timestep %s" % (i+1)

        topo_set=iMesh.EntitySet(t_topo_tag[tsvert],mesh)
        verts=topo_set.getEntities(type=iBase.Type.vertex)

        x_locs=[x[0] for x in mesh.getVtxCoords(verts)]
        y_locs=[x[1] for x in mesh.getVtxCoords(verts)]

        # Find all the data tags
        dtags=mesh.getAllTags(tsvert)
        dtags=[dt for dt in dtags if dt.name.startswith('DATA')]
        ntags=len(dtags)
        nrow=2
        ncol=int(ntags/nrow)+1
        i=1
        for dt in dtags:
            dtc, varname=utils.unpack_data_tag_name(dt.name)
            print "  > Plotting data for %s" % varname
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

            data=utils.get_packed_data(dt, tsvert, dtc)
            if data.size > len(verts): # has levels
                data=data.reshape(md_shp)[33,:,:].reshape(md_shp[1]*md_shp[2])

            data=numpy.ma.masked_equal(data,fill_val,copy=False)
            # apply the scale_factor
            if scale_factor is not None:
                data=data.astype(scale_factor.dtype.char)*scale_factor
                # apply the add_offset
            if add_offset is not None:
                data+=add_offset

            fig.add_subplot(ncol,nrow,i)
            scatter(x_locs,y_locs,c=data,marker='s',cmap=cm.coolwarm,edgecolor='none')
            colorbar(orientation='vertical')
            title("%s (%s)" % (varname,units))

            i+=1

    show(0)