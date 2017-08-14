import numpy as np
# from openravepy import *
import ParticleLib as ptcl
import trimesh
import transformation as tr
# from pylab import *

# env = Environment()
# env.SetViewer('qtcoin')
# woodstick = env.ReadKinBodyXMLFile("woodstick.xml")
# #env.AddKinBody(woodstick,True)
# ion()

# Measurements
o_p = 3e-3
o_n = 10./180.0*np.pi

p1 = [-0.0255,0.007,0.11] # side near y
n1 = [1.,0,0.1]
d1 = [p1,n1,o_p,o_n]

p3 = [0.0252,-0.003,0.12] # side near y
n3 = [-1.,0.002,0]
d3 = [p3,n3,o_p,o_n]

p2 = [0.01,0.005, 0.1707] # top
n2 = [0,0.02,-1.]
d2 = [p2,n2,o_p,o_n]

p4 = [-0.015,-0.043, 0.1692] # top
n4 = [0,0.0,-1]
d4 = [p4,n4,o_p,o_n]

p5 = [0.002,-0.0106,0.102] # side near x
n5 = [0.,1.,0.0]
d5 = [p5,n5,o_p,o_n]

p6 = [0.01,0.0107,0.12] # side near x
n6 = [0.001,-1,0.001]
d6 = [p6,n6,o_p,o_n]

D = [d3,d2,d1,d4,d5,d6]

T = tr.euler_matrix(np.pi/30.,-np.pi/60.,np.pi/70.)
T[:3,3]= np.array([0.001 ,-0.003,-0.002])
for d in D:
    d[0] = np.dot(T[:3,:3],d[0]) + T[:3,3]
    d[1] = np.dot(T[:3,:3],d[1])

extents = [0.05,0.02,0.34]

woodstick = trimesh.creation.box(extents)
# handles = []
# for d in D:
    # handles.append(env.plot3(d[0],0.001, colors=[0, 1, 0],drawstyle=1))
    
# # raw_input("Press Enter to continue...")
# tiny = 1e-5
delta0 = 20
sigma0 = np.diag([0.009, 0.009,0.009,0.04,0.04,0.04],0)
sigma_desired = np.diag([0.0003,0.0003,0.0003,1e-6,1e-6,1e-6],0)
dim = 6 # 6 DOFs
ptcl0 = np.eye(4) 
V0 = ptcl.Region([ptcl0], sigma0)    
M = 6 # No. of particles per delta-neighbohood

list_particles, weights = ptcl.ScalingSeries(woodstick,V0, D, M, sigma0, sigma_desired, dim,visualize = False)

# est = ptcl.VisualizeParticles(woodstick,list_particles, weights, showestimated = False)
maxweight = weights[0]
for w in weights:
  if w > maxweight:
    maxweight = w   

acum_weight = 0
acum_tf = np.zeros((4,4))
weight_threshold = 0.7*maxweight
for i in range(len(list_particles)):
  if weights[i] > weight_threshold:
    p = list_particles[i]
    acum_tf += p*weights[i]
    acum_weight += weights[i]
estimated_particle = acum_tf*(1./acum_weight)
transf = estimated_particle
print "Resulting estimation:\n", transf
print "Real transformation\n", T