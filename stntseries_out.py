#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *
import utils
import argparse


parser = argparse.ArgumentParser(description='Process a structured grid to an imesh representation')
#parser.add_argument('--c', action='store_true', dest='is_coads', help='Process the coards.nc sample grid; otherwise process the ncom.nc sample')
parser.add_argument('--p', action='store_true', dest='do_plot', help='Plot the data for each time and variable')
args=parser.parse_args()

if True:
    in_path = 'test_data/usgs.h5m'
else:
    in_path = 'test_data/ncom.h5m'

mesh=iMesh.Mesh()
mesh.load(in_path)

#ent_sets=mesh.getEntSets()
#for es in ent_sets:
#    report_entset_contents(es)

t_tag=mesh.getTagHandle('TIME_DATA')
# iBase.EntitySet returned from the tag must be 'reinitialized' as an iMesh.EntitySet
t_set=iMesh.EntitySet(t_tag[mesh.rootSet],mesh)

#t_set=mesh.getEntSets()[0]
utils.report_entset_contents(mesh, t_set)

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

ntimes=t_set.getNumChildren()
if ntimes == 0:
    raise Exception("No Children in temporal EntitySet %s" % t_set)

print "\nGeometric Dimension: %s" % mesh.geometricDimension

print "\n# Times: %s" % ntimes

tarr=range(ntimes)

if args.do_plot:

    # This is a timeseries - as such, we need to compile the data for each variable across all the times
    data_map={}

    ts_sets=t_set.getChildren()

    for i in range(ntimes):
        try:
            stn_set = ts_sets[i]
        except:
            stn_set = None

        if stn_set is None:
            raise Exception("The EntitySet %s does not contain a point, cannot process" % ts_sets[i])

        dtags=mesh.getAllTags(stn_set)
        for dt in dtags:
            data=dt[stn_set]
            if not dt.name in data_map:
                data_map[dt.name] = data
            else:
                data_map[dt.name] = numpy.vstack([data_map[dt.name],data])

    nvars=len(data_map)
    nrow=2
    ncol=int(nvars/nrow)+1

    # Apply units, _FillValue, scale_factor, add_offset and plot
    fig = figure()
    i=1
    for var in data_map:
        data=data_map[var]
        dtc, varname=utils.unpack_data_tag_name(data_t.name)
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