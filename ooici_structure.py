#!/usr/bin/env python

"""
@package 
@file ooici_structure.py
@author Christopher Mueller
@brief 
"""

__author__ = 'Christopher Mueller'
__licence__ = 'Apache 2.0'

from itaps import iMesh, iBase
import numpy as np
from numpy import random as rnd
import utils

def make_test_mesh(x,y,z=1):
    mesh=iMesh.Mesh()
    coords=utils.make_coords(x,y,z)
    verts=mesh.createVtx(coords)
    if z is 1:
        vert_arr=utils.make_quadrilateral_vertex_array(verts, x)
        ents,status=mesh.createEntArr(iMesh.Topology.quadrilateral, vert_arr)
    else:
        vert_arr=utils.make_hexahedron_vertex_array(verts, x, y, z)
        ents,status=mesh.createEntArr(iMesh.Topology.hexahedron, vert_arr)

    # Add data to the entities in each cell_dimension
    for i in range(4):
        ents=mesh.getEntities(type=i)
        if len(ents) > 0:
            tag=mesh.createTag('%s_data' % i,1,np.int32)
            m=np.prod([10]*(i+1))
            dat=np.arange(m,m+len(ents),dtype=np.int32)
    #        print 'start: %s, end: %s' % (m, m+100)
    #        dat=rnd.uniform(m,m+100,len(ents)).astype(np.int32)
            print dat
            tag[ents]=dat

    return mesh


class Parameter(object):
    def __init__(self, parent_structure, tag_hndl, ent_hndls, temporal_shape, grid_shape=None):
        self.pstruct=parent_structure
        self.tag_hndl=tag_hndl
        self.ent_hndls=ent_hndls

        cdim_shp=(len(self.ent_hndls),)
        if not isinstance(temporal_shape, tuple): temporal_shape = (temporal_shape,)
        grid_shape=grid_shape or (0,)
        if not isinstance(grid_shape, tuple): grid_shape = (grid_shape,)

        self.ni = BaseIndexing(self, shape=temporal_shape+cdim_shp) # Natural indexing
        self.gi = BaseIndexing(self, shape=temporal_shape+grid_shape) # Non-natural (grid) indexing

    @property
    def name(self):
        return self.tag_hndl.name

    @property
    def shape(self):
        return self.ni.shape, self.gi.shape

class BaseIndexing(object):
    def __init__(self, parent_parameter, shape):
        self.valid=True
        self.pparam=parent_parameter
        self.shape=shape
        if 0 in shape:
            self.valid=False
            return

        self.ent_hndls=self.pparam.ent_hndls.copy().reshape(shape[1:])

    def __getitem__(self, index):
        if not self.valid:
            raise Exception('Invalid slicing of parameter "%s"' % self.pparam.name)

        if not isinstance(index, tuple): index = (index,)

        print 'index: %s' % (index,)

        # TODO: Temporarily remove time slice (1st member of index)
        sents=self.ent_hndls[index[1:]]
        print 'sents: %s' % sents
        return self.pparam.tag_hndl[sents.reshape(np.prod(sents.shape))].reshape(sents.shape)

    def __repr__(self):
        return 'entity_handles: %s\nshape: %s' % (self.ent_hndls,self.shape,)

#class GridIndexing(BaseIndexing):
#    def __init__(self, dims=None):
#        BaseIndexing.__init__(self, dims=dims)
#
#class NaturalIndexing(BaseIndexing):
#    def __init__(self, dims=None):
#        BaseIndexing.__init__(self, dims=dims)


class Structure(object):
    def __init__(self, mesh=None, grid_dimensions=None):
#        if grid_dimensions is None: #TODO: Temporary, replace with grid_dimensions or 'default' statement
#            x=3
#            y=3
#            z=3
#            if z is 1:
#                zp=1
#            else:
#                zp=z-1
#
#            self.gshp=((x,y,z),(0,),(x-1,y-1,zp),(x-1,y-1,zp))
#        else:
#            self.gshp=grid_dimensions

#        self.gshp=((3,1,1),(0,),(0,),(0,))
#        self.gshp=((3,3,1),(0,),(2,2,1),(0,))
        self.gshp=((4,4,1),(0,),(3,3,1),(0,))
#        self.gshp=((20,30,1),(0,),(19,29,1),(0,))
#        self.gshp=((3,3,2),(0,),(0,),(2,2,1))
#        self.gshp=((3,3,3),(0,),(0,),(2,2,2))
#        self.gshp=((3,3,4),(0,),(0,),(2,2,3))
#        self.gshp=((3,4,4),(0,),(0,),(2,3,3))

        self.mesh = mesh or make_test_mesh(self.gshp[0][0], self.gshp[0][1], self.gshp[0][2])

        self.tshp=(1,)

        self.parameters={}
        for i in range(4):
            ents=self.mesh.getEntities(type=i)
            if len(ents) > 0:
                tags=self.mesh.getAllTags(ents[0])
                for tag in tags:
                    self.parameters[tag.name] = Parameter(self, tag, ents, self.tshp, self.gshp[i])

    def __repr__(self):
        return '# Parameters: %s\n' % len(self.parameters)