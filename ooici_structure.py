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
        tag=mesh.createTag('%s_data' % i,1,np.int32)
        m=np.prod([10]*(i+1))
        dat=np.arange(m,m+len(ents),dtype=np.int32)
        #        print 'start: %s, end: %s' % (m, m+100)
        #        dat=rnd.uniform(m,m+100,len(ents)).astype(np.int32)
        print dat
        tag[ents]=dat

    return mesh

class Structure(object):
    def __init__(self, mesh=None, grid_dimensions=None):
        if grid_dimensions is None: #TODO: Temporary, replace with grid_dim or 'default' statement
            x=4
            y=4
            z=1
            if z is 1:
                z1=1
            else:
                z1=z-1

            self.gdims=((x,y,z),(x-1,y-1,z),(x-1,y-1,z),(0,))
        else:
            self.gdims=grid_dimensions

        #        self.gdims=((3,1,1),(2,1,1),(0,),(0,))
        #        self.gdims=((3,3,1),(2,2,1),(2,2,1),(0,))
        #        self.gdims=((4,4,1),(3,3,1),(3,3,1),(0,))
        #        self.gdims=((20,30,1),(19,29,1),(19,29,1),(0,))
        #        self.gdims=((3,3,2),(2,2,1),(2,2,1),(2,2,1))
        #        self.gdims=((3,3,3),(2,2,2),(2,2,2),(2,2,2))
        #        self.gdims=((3,3,4),(2,2,3),(2,2,3),(2,2,3))
        #        self.gdims=((3,4,4),(2,3,3),(2,3,3),(2,3,3))


        self.mesh = mesh or make_test_mesh(self.gdims[0][0], self.gdims[0][1], self.gdims[0][2])

        self.tdim=(1,)
        cnt=np.bincount(self.mesh.getEntType(self.mesh.getEntities()))
        if cnt.size < 4:
            cnt=np.hstack([cnt,[0]*(4-cnt.size)])
        self.cdims=[(int(i),) for i in cnt]

    def __getitem__(self, index):
        if not isinstance(index, tuple): index = (index,)

        if not type(index[0]) is tuple:
            raise Exception("First member must be an tuple of type (int, bool) indicating the (cell_dimension, natural_indexing)")

        flags=index[0]
        nat_ind = True
        cell_dim = 0
        if len(flags) is 2:
            if type(flags[1]) is bool:
                cell_dim = flags[0]
                nat_ind = flags[1]
            elif type(flags[0]) is bool:
                nat_ind = flags[0]
                cell_dim = flags[1]
        elif len(flags) is 1:
            if type(flags[0]) is bool:
                nat_ind = flags[0]
            else:
                cell_dim = flags[0]

        # Remove the 'flag' from the index
        index=index[1:]

        # Sanity check
        if cell_dim > 3 or cell_dim < 0:
            raise Exception('cell dimension must be between 0 & 3 (inclusive)')

        print 'nat_ind: %s, cell_dim: %s' % (nat_ind, cell_dim)

        for slice_ in index:
            print '%s (%s)' % (slice_,type(slice_))

        # Ignore time for now
        # TODO: eventually, must determine spatial indices and then concatenate (vstack/hstack, possibly by dimension)
        # the extracted data across desired times
        index=index[1:]

        # Get the tag and the array of entity handles for the specified cell_dimension
        tag=self.mesh.getTagHandle('%s_data' % cell_dim)
        ents=self.mesh.getEntities(type=cell_dim)

        if not nat_ind:
            ents=ents.reshape(self.gdims[cell_dim])
        #            raise Exception('Only natural-indexing is currently supported')

        #        print '>> all_ents: %s' % ents
        sents=ents[index]
        #        print '>> slice_ents: %s shp: %s' % (sents,sents.shape)
        return tag[sents.reshape(np.prod(sents.shape))]

    @property
    def shape0(self):
        return self.tdim + self.cdims[0]

    @property
    def shape1(self):
        return self.tdim + self.cdims[1]

    @property
    def shape2(self):
        return self.tdim + self.cdims[2]

    @property
    def shape3(self):
        return self.tdim + self.cdims[3]

    @property
    def shapeG0(self):
        return self.tdim + self.gdims[0]

    @property
    def shapeG1(self):
        return self.tdim + self.gdims[1]

    @property
    def shapeG2(self):
        return self.tdim + self.gdims[2]

    @property
    def shapeG3(self):
        return self.tdim + self.gdims[3]

    def __repr__(self):
        return 'cdim0shp: %s\n'\
               'cdim1shp: %s\n'\
               'cdim2shp: %s\n'\
               'cdim3shp: %s\n'\
               'gshp0: %s\n'\
               'gshp1: %s\n'\
               'gshp2: %s\n'\
               'gshp3: %s\n' % (self.shape0,self.shape1,self.shape2,self.shape3,self.shapeG0,self.shapeG1,self.shapeG2,self.shapeG3)