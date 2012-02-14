#!/usr/bin/env python

from itaps import iBase, iMesh, iGeom
from netCDF4 import Dataset
import numpy
from pylab import *

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

#TODO: this can be a static utility method in a "UniformGridUtils" type class
def centroid_to_vertex_coords(x_coords, y_coords):
    dxarr=(x_coords[1:]-x_coords[0:-1])
    if dxarr.std() != 0.0:
        raise Exception("Non-uniform x array")
    dx=dxarr.mean()
    x_coords-=(dx*0.5)
    x_coords=numpy.append(x_coords,[x_coords[-1]+dx])

    dyarr=(y_coords[1:]-y_coords[0:-1])
    if dyarr.std() != 0.0:
        raise Exception("Non-uniform y array")
    dy=dyarr.mean()
    y_coords-=(dy*0.5)
    y_coords=numpy.append(y_coords,[y_coords[-1]+dy])
    
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

def transform_dataset(ds, var_map, out_path):
    mesh=iMesh.Mesh()

    coords_map=var_map['coords']
    if coords_map['z_var']:
        zarr=ds.variables[coords_map['z_var']][:]
        z_cnt=len(zarr)

    x_coords=ds.variables[coords_map['x_var']][:]
    y_coords=ds.variables[coords_map['y_var']][:]
    x_coords, y_coords = centroid_to_vertex_coords(x_coords=x_coords, y_coords=y_coords)
    x_cnt=len(x_coords)
    y_cnt=len(y_coords)

    coords=[]
    icoords=[]
    z=0
    for y in range(y_cnt):
        icoords=[]
        for x in range(x_cnt):
            icoords+=[[x_coords[x],y_coords[y],z]]
        coords+=icoords
    del icoords

    # Create the vertices
    verts=mesh.createVtx(coords)
    nverts=len(verts)
    # Add the vertices as an EntitySet that is ordered and doesn't contain duplicates
    vert_set=mesh.createEntSet(ordered=True)
    vert_set.add(verts)

    # Create quadrilateral entities
    # Build the appropriate vertex-array from the vertices
    vert_arr = make_quadrilateral_vertex_array(verts=verts, x_cnt=x_cnt, y_cnt=y_cnt)

    quads,status=mesh.createEntArr(iMesh.Topology.quadrilateral,vert_arr)
    # Add the quads as an EntitySet that is unordered and may contain duplicates
    quad_set=mesh.createEntSet(ordered=False)
    quad_set.add(quads)
    # Add the vert_set
    quad_set.add(vert_set)
    nquads=len(quads)

    print "%d vertices, %d faces, %d edges" % (mesh.getNumOfType(iBase.Type.vertex),
                                               mesh.getNumOfType(iBase.Type.face),
                                               mesh.getNumOfType(iBase.Type.edge))

    ## Assign the dataset data
    for varn in var_map['data']:
        var=ds.variables[varn]
        var.set_auto_maskandscale(False)
        dt=var.dtype
        tag=None
        if dt in [numpy.byte,numpy.int8,numpy.int16,numpy.int32,numpy.float32,numpy.float64]:
            if len(var.shape) == 4:
                arr=var[0,0,:,:].reshape(nquads)
            else:
                arr=var[0,:,:].reshape(nquads)

            if dt == numpy.int16:
                tag=mesh.createTag('DATA_'+varn,1,numpy.int32)
                tag[quads]=arr.astype(numpy.int32)
            elif dt == numpy.float32:
                tag=mesh.createTag('DATA_'+varn,1,numpy.float64)
                tag[quads]=arr.astype(numpy.float64)
            else:
                tag=mesh.createTag('DATA_'+varn,1,dt)
                tag[quads]=arr
        else:
            raise Exception("Type %s not supported" % dt)

        if tag:
            # add var attribute tags to the data tag
            for attn in var.ncattrs():
                process_attribute(mesh, "VAR_ATT_%s::%s" % (varn, attn), var.getncattr(attn))

    # Global Attributes
    for gattn in ds.ncattrs():
        process_attribute(mesh, "GBL_ATT_"+gattn, ds.getncattr(gattn))

    mesh.save(out_path)
    print "Saved to %s" % out_path

import argparse
parser = argparse.ArgumentParser(description='Process a structured grid to an imesh representation')
parser.add_argument('--c', action='store_true', dest='is_coads', help='If the coards.nc sample grid should be processed; otherwise process the ncom.nc sample')
args=parser.parse_args()

# Setup the config for this dataset - this comes with the ExternalDataset (info provided by the registrant)
var_map={}
if args.is_coads:
    var_map['coords']={'t_var':'TIME','x_var':'COADSX','y_var':'COADSY','z_var':None}
    var_map['data']=['SST','AIRT','SPEH','WSPD','UWND','VWND','SLP']
    in_path='test_data/coads.nc'
    out_path='test_data/coads.h5m'
else:
    var_map['coords']={'t_var':'time','x_var':'lon','y_var':'lat','z_var':'depth'}
    var_map['data']=['salinity','surf_el','water_temp','water_u','water_v']
    in_path='test_data/ncom.nc'
    out_path='test_data/ncom.h5m'

# Load and process the dataset
ds=Dataset(in_path)
transform_dataset(ds, var_map, out_path)
ds.close()
