#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
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
    in_path = 'test_data/coads.h5m'
elif args.is_hfr:
    in_path = 'test_data/hfr.h5m'
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

if args.do_plot:
    if len(args.time_indices) == 0:
        args.time_indices = range(ntimes)

    print "Plot time indices: %s" % args.time_indices

    ts_sets=t_set.getChildren()

    ## Save the figures off to a pdf file
    #from matplotlib.backends.backend_pdf import PdfPages
    #pdfp=PdfPages(in_path.replace('.h5m','.pdf'))
    for i in args.time_indices:
        if i >= ntimes:
            print "Cannot Plot: Index %s is outside the bounds of the time array (max is %s)" % (i, ntimes-1)
            continue
        print "Plotting data for time index %s" % i
        try:
            set=ts_sets[i]
        except:
            set = None

        if set is None:
            raise Exception("The EntitySet %s does not contain quadrilaterals, cannot process" % ts_sets[i])

        fig=figure()
#        fig.suptitle="Timestep %s" % (i+1)
        from matplotlib import cm
        from matplotlib.collections import PolyCollection

        # We know this is a rectilinear grid, which means we know there are quadrilateral entities,
        # so get them, get the data tags associated with them, and then loop through them to plot the data
        #quads=mesh.getEntities(topo=iMesh.Topology.quadrilateral)

        quads=set.getEntities(topo=iMesh.Topology.quadrilateral)

        # Find all the data tags
        dtags=mesh.getAllTags(set)
        ntags=len(dtags)
        nrow=2
        ncol=int(ntags/nrow)+1
        for i in range(ntags):
            data_t=dtags[i]
            dtc, varname=utils.unpack_data_tag_name(data_t.name)
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

            data=utils.get_packed_data(data_t, set, dtc)
#            data=data_t[set]

            data=numpy.ma.masked_equal(data,fill_val,copy=False)
            # apply the scale_factor
            if scale_factor is not None:
                data=data.astype(scale_factor.dtype.char)*scale_factor
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

    #    fig.savefig(pdfp, format='pdf')

    show(0)

#pdfp.close()
#
## Open the resultant pdf
#import os
#os.system('open %s' % in_path.replace('.h5m','.pdf'))

#print "# of EntitySets at rootSet: %s" % len(ent_sets)
#
#tags=[]
#i=0
#for es in ent_sets:
#    etags=mesh.getAllTags(es)
#    print "# of tags for EntitySet %i: %s" % (i, len(etags))
#    if len(etags) != 0:
#        tags.append(etags)
#    i+=1
#
#print "Total # of EntitySet Tags: %s" % len(tags)


#quads=mesh.getEntities(topo=iMesh.Topology.quadrilateral)
#print "NumOfQuads: %s" % len(quads)

#quad_vert_list=mesh.getEntAdj(quads, iBase.Type.vertex)
#quad_coords=numpy.empty((len(quads),4,3))
#i=0
#for qv in quad_vert_list:
#    quad_coords[i,:,:]=mesh.getVtxCoords(qv)
#    i+=1

#tag=mesh.getTagHandle('DATA_water_temp')
#data=tag[quads]

#subplot(2,1,1)
#for coords in quad_coords:
#    cp=coords.copy()
#    cp.resize(5,3)
#    cp[4,:]=cp[0,:]
#    plot(cp[:,0],cp[:,1],hold=True)
#
#title('quadrilateral bounds')
