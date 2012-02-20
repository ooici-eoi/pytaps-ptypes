import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from itaps import iBase, iMesh, iGeom

def try_plot(mesh):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    #%run mesh_gen.py 2 2 3
    regions=mesh.getEntities(type=iBase.Type.region)
    for r in regions:
        faces=mesh.getEntAdj(r,iBase.Type.face)
        i=1
        for f in faces:
            coords=mesh.getVtxCoords(mesh.getEntAdj(f,iBase.Type.vertex))
            x=np.vstack([coords[:,[0]],coords[0,[0]]]).reshape(1,5)
            y=np.vstack([coords[:,[1]],coords[0,[1]]]).reshape(1,5)
            z=np.vstack([coords[:,[2]],coords[0,[2]]]).reshape(1,5)

            ## "unfilled" surfaces
            x=np.vstack([x,x])
            y=np.vstack([y,y])
            z=np.vstack([z,z])

            ## Try for solid surfaces
#            if i is 2:
#                x=np.vstack([x,[1,1,1,1,1]])
#            else:
#                x=np.vstack([x,[0,0,0,0,0]])
#            if i is 3:
#                y=np.vstack([y,[1,1,1,1,1]])
#            else:
#                y=np.vstack([y,[0,0,0,0,0]])
#            if i is 6:
#                z=np.vstack([z,[1,1,1,1,1]])
#            else:
#                z=np.vstack([z,[0,0,0,0,0]])

#            print 'x=%s' % x
#            print 'y=%s' % y
#            print 'z=%s\n' % z

            ax.plot_surface(x,y,z)
            ax.plot_wireframe(x,y,z)
            i+=1

    plt.show(0)