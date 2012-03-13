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
from ordereddict import OrderedDict

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
    def __init__(self, parent_structure, tag_handle, entity_handles, vertex_entity_handles, temporal_shape, grid_shape=None):
        self._pstruct=parent_structure
        self._tag_hndl=tag_handle
        self._ent_hndls=entity_handles
        self._vent_hndls=vertex_entity_handles

        cdim_shp=(len(self._ent_hndls),)
        if not isinstance(temporal_shape, tuple): temporal_shape = (temporal_shape,)
        grid_shape=grid_shape or (0,)
        if not isinstance(grid_shape, tuple): grid_shape = (grid_shape,)

        self.ni = ParameterIndexing(self, shape=temporal_shape+cdim_shp) # Natural indexing
        self.gi = ParameterIndexing(self, shape=temporal_shape+grid_shape) # Non-natural (grid) indexing

        # TODO: Finish adding coords field that return spatiotemporal coordinates
        self.ncoords = CoordinateIndexing(self, shape=temporal_shape+cdim_shp)
        self.gcoords = CoordinateIndexing(self, shape=temporal_shape+grid_shape)

    @property
    def name(self):
        return self._tag_hndl.name

    @property
    def shape(self):
        return 'Natural Indexing: %s, Grid Indexing: %s' % (self.ni.shape, self.gi.shape)

class CoordinateIndexing(object):
    def __init__(self, parent_parameter, shape):
        self._valid=True
        self._pparam=parent_parameter
        self._mesh=self._pparam._pstruct.mesh
        self.shape=shape

        # Invalidate the IndexingStrategy if any of the members of shape are 0
        if 0 in shape:
            self._valid=False
            return

        # Make a copy of the entity_handles for this indexing and reshape to shape
        self._ent_hndls=self._pparam._ent_hndls.copy().reshape(shape[1:])

    def __getitem__(self, slice_):
        # TODO: Why does this need to be different than the other indexing?
        # It just returns something different, which can be explained to the developer
        # at the field level (since indexing is hidden anyhow)
        #
        # Because slicing won't work using the same shape - need to differentiate :(
        # - but it will since you'd be looking to get ALL coordinates for the cell_dim of interest...
        # --> slice on celldim and THEN get vertices for those features... which still requires a different procedure
        if not self._valid:
            raise Exception('Invalid slicing of parameter "%s"' % self._pparam.name)

        if not isinstance(slice_, tuple): slice_ = (slice_,)

        print 'slice_: %s' % (slice_,)

        # TODO: Temporarily remove time slice (1st member of slice_)
        slice_=slice_[1:]

        # Get the entities pertaining to the requested slice
#        print 'ent_handles_shp: %s' % (self._ent_hndls.shape,)
        sents=self._ent_hndls[slice_]
#        print 'sents_shp: %s' % (sents.shape,)

        # Process the vertices in natural indexing, then reshape at the end
        if self._mesh.getEntType(sents.flat[0]) is 0:
            # cell_dimension 0 is a special case
            vents=sents.reshape(np.prod(sents.shape))
#            print 'vents: %s' % vents
            odim=len(vents)

            carr=np.empty([odim, 3])
            for i in xrange(len(vents)):
#                print '\t%s' % vents[i]
                cds=self._mesh.getVtxCoords(vents[i])
#                print '\t\t%s' % cds
                carr[i]=cds

#            print 'carr: %s   s: %s' % (carr.shape, sents.shape+(3,))
            carr=carr.reshape(sents.shape+(3,))
#            print '>>>> %s' % carr
        else:
            # the higher-order cell_dimensions can be handled the same way
            vents=self._mesh.getEntAdj(sents.reshape(np.prod(sents.shape)), type=0)
            nvdim=len(vents[0])

#            print 'vents: %s' % vents
            odim=len(vents)

            carr=np.empty([odim, nvdim, 3])
            for i in xrange(len(vents)):
#                print '\t%s' % vents[i]
                cds=self._mesh.getVtxCoords(vents[i])
#                print '\t\t%s' % cds
                for j in xrange(len(cds)):
                    carr[i,j]=cds[j]

#            print 'carr: %s   s: %s' % (carr.shape, sents.shape+(nvdim, 3,))
            carr=carr.reshape(sents.shape+(nvdim, 3,))
#            print '>>>> %s' % carr

        return carr

    def __repr__(self):
        return 'shape: %s' % (self.shape,)


class ParameterIndexing(object):
    def __init__(self, parent_parameter, shape):
        self._valid=True
        self._pparam=parent_parameter
        self.shape=shape
#        self.shape=tuple(reversed(shape))
        
        # Invalidate the IndexingStrategy if any of the members of shape are 0
        if 0 in shape:
            self._valid=False
            return

        # Make a copy of the entity_handles for this indexing and reshape to shape
        self._ent_hndls=self._pparam._ent_hndls.copy().reshape(shape[1:])

    def __getitem__(self, slice_):
        if not self._valid:
            raise Exception('Invalid slicing of parameter "%s"' % self._pparam.name)

        if not isinstance(slice_, tuple): slice_ = (slice_,)

        print 'slice_: %s' % (slice_,)

        # TODO: Temporarily remove time slice (1st member of slice_)
        slice_=slice_[1:]

        # Get the entities pertaining to the requested slice
#        print 'ent_handles_shp: %s' % (self._ent_hndls.shape,)
        sents=self._ent_hndls[slice_]
#        print 'sents_shp: %s' % (sents.shape,)

        # Return the data for the appropriate entities
        return self._pparam._tag_hndl[sents.reshape(np.prod(sents.shape))].reshape(sents.shape)

    def __repr__(self):
        return 'shape: %s' % (self.shape,)

class Structure(object):
    def __init__(self, mesh=None, grid_dimensions=None):
        if grid_dimensions is None:
#            grid_dimensions=((3,1,1),(0,),(0,),(0,))
#            grid_dimensions=((3,3,1),(0,),(2,2,1),(0,))
#            grid_dimensions=((4,4,1),(0,),(3,3,1),(0,))
#            grid_dimensions=((3,3),(0,),(2,2),(0,))
#            grid_dimensions=((4,4),(0,),(3,3),(0,))
            grid_dimensions=((5,5),(0,),(4,4),(0,))
#            grid_dimensions=((20,30,1),(0,),(19,29,1),(0,))
#            grid_dimensions=((3,3,2),(0,),(0,),(2,2,1))
#            grid_dimensions=((3,3,3),(0,),(0,),(2,2,2))
#            grid_dimensions=((3,3,4),(0,),(0,),(2,2,3))
#            grid_dimensions=((3,4,4),(0,),(0,),(2,3,3))

        if len(grid_dimensions[0]) is 3:
            z=grid_dimensions[0][2]
        else:
            z=1

        self.gshp = grid_dimensions
        if mesh is None:
            mesh = make_test_mesh(self.gshp[0][0], self.gshp[0][1], z)

        self.mesh = mesh
        print 'mesh: %s' % self.mesh

        self.tshp=(1,)

        self.parameters=OrderedDict()
        for i in range(4):
            print 'cell_dim: %s' % i
            ents=self.mesh.getEntities(type=i)
            if len(ents) > 0:
                # TODO: ASSUMES ALL TAGS ARE ON ALL ENTITIES
                tags=self.mesh.getAllTags(ents[0])
                if i is 0:
                    vents=ents.copy()
                else:
                    vents=self.mesh.getEntAdj(ents, type=0)
                for tag in tags:
                    print '\ttag_name: %s\n\t  %s\n\t  %s' % (tag.name, len(ents), len(vents))
                    self.parameters[tag.name] = Parameter(self, tag, ents, vents, self.tshp, self.gshp[i])


    def __repr__(self):
        return '# Parameters: %s\n' % len(self.parameters)