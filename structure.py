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
from collections import OrderedDict

def unpack_data_tag_name(data_tag_name):
    varname=data_tag_name.replace('DATA_','')
    return varname.split('_', 2)

class Parameter(object):
    def __init__(self, parent_structure, tag_handle, entity_handles):
        self._pstruct=parent_structure
        self._tag_hndl=tag_handle
        self._ent_hndls=entity_handles
        self._index_keys=[]

        # Break apart the tag to it's component info
        self.cell_dim, self.data_type, self.name = unpack_data_tag_name(self._tag_hndl.name)

        self._init_indexing()

    def _init_indexing(self):
        # First remove any indexing attributes currently present
        for k in self._index_keys:
            delattr(self, k)
        self._index_keys=[]

        # Get the current set of indexings, make an attribute for each and add the name to self._index_keys
        cell_indexings=self._pstruct.indexing[self.cell_dim]
        for key in cell_indexings:
            ik='i{0}'.format(key)
            ck='i{0}_CDS'.format(key)
            setattr(self, ik, ParameterIndexing(self, cell_indexings[key]))
            setattr(self, ck, CoordinateIndexing(self, cell_indexings[key]))
            self._index_keys.append(ik)
            self._index_keys.append(ck)

    def reinitialize(self):
        print "reinitializing parameter {0}".format(self.name)
        self._init_indexing()

    @property
    def shape(self):
        s=''
        for k in self._index_keys:
            s+='{0} | {1}; '.format(k, getattr(self, k).shape)

        return s

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
        self._tverts=self._pparam._pstruct._t_verts

    def __getitem__(self, slice_):
        if not self._valid:
            raise Exception('Invalid slicing of parameter "%s"' % self._pparam.name)

        if not isinstance(slice_, tuple): slice_ = (slice_,)

        print 'slice_: %s' % (slice_,)

        # TODO: Temporarily remove time slice (1st member of slice_) - assumes time-invariant spatial topology
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
        self._tverts=self._pparam._pstruct._t_verts

    def __getitem__(self, slice_):
        if not self._valid:
            raise Exception('Invalid slicing of parameter "%s"' % self._pparam.name)

        if not isinstance(slice_, tuple): slice_ = (slice_,)

        print 'slice_: %s' % (slice_,)

        # get the time verticies based on the first member of the slice
        tverts=self._tverts[slice_[0]]

        try:
            ntverts=len(tverts)
        except Exception:
            ntverts=1

        print 'num time_verts: %s' % ntverts
#        slice_=slice_[1:]

        # Get the entities pertaining to the requested slice
#        print 'ent_handles_shp: %s' % (self._ent_hndls.shape,)
#        sents=self._ent_hndls[slice_]
#        print 'sents_shp: %s' % (sents.shape,)

        # Return the data for the appropriate entities
        nshp=(ntverts,)+self.shape[1:]
        print nshp
        return utils.get_packed_data(self._pparam._tag_hndl, tverts, self._pparam.data_type).reshape(nshp)[(slice(None),)+slice_[1:]]

    def __repr__(self):
        return 'shape: %s' % (self.shape,)

class Structure(object):
    def __init__(self, mesh_in, index_key):
        if isinstance(mesh_in, str or unicode):
            try:
                self.mesh=iMesh.Mesh()
                self.mesh.load(mesh_in)
            except Exception as ex:
                raise ex
        elif isinstance(mesh_in, iMesh.Mesh):
            self.mesh=mesh_in
        else:
            raise TypeError('mesh_in is of unknown type: {0}'.format(type(mesh_in)))

        print 'mesh: %s' % self.mesh

        if isinstance(index_key, str or unicode):
            from ConfigParser import SafeConfigParser
            parser=SafeConfigParser()
            parser.read('dataset_out.config')
            hindexing=eval(parser.get(index_key, 'base_indexing'))
            if not isinstance(hindexing, dict):
                raise TypeError('type of option {0} in dataset_out.config[base_indexing] is invalid: {1}'.format(index_key, type(hindexing)))
        else:
            raise TypeError('index_key is of unsupported type: {0}'.format(type(index_key)))

        # Get Time Tags
        t_tag=self.mesh.getTagHandle('T0')
        time_topo_set=iMesh.EntitySet(t_tag[self.mesh.rootSet], self.mesh)
        self._t_verts=time_topo_set.getEntities(type=0)
        print 'num_times: %s' % len(self._t_verts)
        self.tshp=(len(self._t_verts),)

        self.parameters=OrderedDict()
        self.indexing={}
#        for i in xrange(4):
#            topo_name='S{0}'.format(i)
#            self.indexing[topo_name] = {}
        for topo_key in hindexing:
            try:
                tag=self.mesh.getTagHandle(topo_key)
            except iBase.TagNotFoundError:
                continue
            ents=utils.getEntitiesByTag(self.mesh, tag)
            print '#_ents for topo_key {0}: {1}'.format(topo_key, len(ents))
            self.indexing[topo_key]={'NATURAL':(self.tshp+(len(ents),)),
                                  'GRID':(self.tshp+hindexing[topo_key])}
            if len(ents) > 0:
                tags=self.mesh.getAllTags(self._t_verts[0])
                dtags=[dt for dt in tags if dt.name.startswith('DATA_{0}'.format(topo_key))]
                print 'tags on {0}: {1}'.format(topo_key, [t.name for t in dtags])
                for tag in dtags:
                    p=Parameter(self, tag, ents)
                    print '\t%s\t%s\t%s' % (tag.name, p.name, len(ents))
                    self.parameters[p.name] = p

    def reinitialize(self):
        for pk in self.parameters:
            self.parameters[pk].reinitialize()

    def __repr__(self):
        return '# Parameters: %s\n' % len(self.parameters)