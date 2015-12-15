import numpy as np
import scipy.linalg
# Plots
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt


def TranValidate(T):
  """
  Validate T
  @type T:    array 4x4 
  @param T:   transformation matrix
  """
  raise NotImplementedError


def RotValidate(C):
  raise NotImplementedError


def TranAd(T):
  """
  Compute Adjoint of 4x4 transformation matrix, return a 6x6 matrix
  @type T:    array 4x4 
  @param T:   transformation matrix
  """
  C = T[:3,:3]
  r = T[:3,3]
  AdT = np.zeros([6,6])
  AdT[:3,:3] = C
  AdT[:3,3:] = np.dot(Hat(r),C)
  AdT[3:,3:] = C
  return AdT


def Hat(vec):
  """
  hat operator - return skew matrix (return 3x3 or 4x4 matrix) from vec
  @param vec:   vector of 3 (rotation) or 6 (transformation)
  """
  if vec.shape[0] == 3: # skew from vec
    return np.array([[0,-vec[2],vec[1]],[vec[2],0,-vec[0]],[-vec[1],vec[0],0]])
  elif vec.shape[0] == 6:
    vechat = np.zeros((4,4))
    vechat[:3,:3] = Hat(vec[3:])
    vechat[:3,3] = vec[:3]
    return vechat
  else:
    raise ValueError("Invalid vector length for hat operator\n")


def VecFromSkew(r):
  return np.array([r[2,1],r[0,2],r[1,0]])


def CurlyHat(vec):
  """
  Builds the 6x6 curly hat matrix from the 6x1 input
  @param vec:          a 6x1 vector xi
  @param veccurlyhat:  a 6x6 matrix 
  """
  veccurlyhat = np.zeros((6,6))
  veccurlyhat[:3,:3] = Hat(vec[3:])
  veccurlyhat[:3,3:] = Hat(vec[:3])
  veccurlyhat[3:,3:] = Hat(vec[3:])
  return veccurlyhat


def CovOp1(A):
  """ 
  Covariance operator 1 - eq. 44
  """
  return -np.trace(A)*np.eye(3) + A

 
def CovOp2(A,B):
  """ 
  Covariance operator 2 - eq. 45
  """
  return np.dot(CovOp1(A),CovOp1(B)) + CovOp1(np.dot(B,A))


def TranToVec(T):
  """
  Compute the matrix log of the transformation matrix T
  Convert from T to xi
  @param T:       4x4
  @param return:  return a 6x1 vector in tangent coordinates computed from T.
  """
  C = T[:3,:3]
  r = T[:3,3]
  
  phi = RotToVec(C)
  invJ = VecToJacInv(phi)
  
  rho = np.dot(invJ,r)
  return np.hstack([rho,phi])


def RotToVec(C):
  """
  Compute the matrix log of the rotation matrix C
  @param C:      3x3
  @param return: Return a 3x1 vector (axis*angle) computed from C
  """
  #rotValidate(C)
  if(abs(np.trace(C)+1)>1e-10):
    if(np.linalg.norm(C-np.eye(3))<=1e-10):
      return np.zeros(3)
    else:
      phi = np.arccos((np.trace(C)-1)/2)
      return VecFromSkew(phi/(2*np.sin(phi))*(C-C.T))
  else:
    eigval, eigvect = np.linalg.eig(C)
    for (i,val) in enumerate(eigval):
      if abs((val-1)) <= 1e-10:
        return pi*np.real(eigvect[:,i])


def VecToRot(phi):
  """
  Return a rotation matrix computed from the input vec (phi 3x1)
  @param phi: 3x1 vector (input)
  @param C:   3x3 rotation matrix (output)
  """
  tiny = 1e-12
  #check for small angle
  nr = np.linalg.norm(phi)
  if nr < tiny:
    #~ # If the angle (nr) is small, fall back on the series representation.
    #~ # In my experience this is very accurate for small phi
    C = VecToRotSeries(phi,10)
    #~ #print 'VecToRot:  used series method'
  else:
    R = Hat(phi)
    C = np.eye(3) + np.sin(nr)/nr*R + (1-np.cos(nr))/(nr*nr)*np.dot(R,R)
  return C


def VecToRotSeries(phi, N):
  """"
  Build a rotation matrix using the exponential map series with N elements in the series 
  @param phi: 3x1 vector
  @param N:   number of terms to include in the series
  @param C:   3x3 rotation matrix (output)
  """
  C = np.eye(3)
  xM = np.eye(3)
  cmPhi = Hat(phi)
  for n in range(N):
    xM = np.dot(xM, cmPhi)/(n+1)
    C = C + xM
  # Project the resulting rotation matrix back onto SO(3)
  C = np.dot(C,np.linalg.inv(scipy.linalg.sqrtm(np.dot(C.T,C))))
  return C


def cot(x):
  return 1./np.tan(x)

  
def VecToJacInv(vec):
  """
  Construction of the 3x3 J^-1 matrix or 6x6 J^-1 matrix.
  @param vec:  3x1 vector or 6x1 vector (input)
  @param invJ: 3x3 inv(J) matrix or 6x6 inv(J) matrix (output)
  """
  tiny = 1e-12
  if vec.shape[0] == 3: # invJacobian of SO3
    phi = vec
    nr = np.linalg.norm(phi)
    if nr < tiny:
      # If the angle is small, fall back on the series representation
      invJSO3 = VecToJacInvSeries(phi,10)
    else:
      axis = phi/nr
      invJSO3 = 0.5*nr*cot(nr*0.5)*np.eye(3) + (1- 0.5*nr*cot(0.5*nr))*axis[np.newaxis]*axis[np.newaxis].T- 0.5*nr*Hat(axis)
    return invJSO3
  elif vec.shape[0] == 6: # invJacobian of SE3
    rho = vec[:3]
    phi = vec[3:]
    
    nr = np.linalg.norm(phi)
    if nr < tiny:
      # If the angle is small, fall back on the series representation
      invJSO3 = VecToJacInvSeries(phi,10)
    else:
      invJSO3 = VecToJacInv(phi)
    Q = VecToQ(vec)
    invJSE3 = np.zeros((6,6))
    invJSE3[:3,:3] = invJSO3
    invJSE3[:3,3:] = -np.dot(np.dot(invJSO3,Q), invJSO3)
    invJSE3[3:,3:] = invJSO3
    return invJSE3
  else:
    raise ValueError("Invalid input vector length\n")


def VecToJacInvSeries(vec,N):
  """
  Construction of the 3x3 J^-1 matrix or 6x6 J^-1 matrix. Series representation.
  @param vec:  3x1 vector or 6x1 vector
  @param N:    number of terms to include in the series
  @param invJ: 3x3 inv(J) matrix or 6x6 inv(J) matrix (output)
  """
  if vec.shape[0] == 3: # invJacobian of SO3
    invJSO3 = np.eye(3)
    pxn = np.eye(3)
    px = Hat(vec)
    for n in range(N):
      pxn = np.dot(pxn,px)/(n+1)
      invJSO3 = invJSO3 + BernoulliNumber(n+1)*pxn
    return invJSO3
  elif vec.shape[0] == 6: # invJacobian of SE3
    invJSE3 =np.eye(6)
    pxn = np.eye(6)
    px = CurlyHat(vec)
    for n in range(N):
      pxn = np.dot(pxn,px)/(n+1)
      invJSE3 = invJSE3 + BernoulliNumber(n+1)*pxn
    return invJSE3
  else:
    raise ValueError("Invalid input vector length\n")


def BernoulliNumber(n):
  """
  Generate Bernoulli number
  @param n:  interger (0,1,2,...)
  """
  from fractions import Fraction as Fr
  if n == 1: return -0.5
  A = [0] * (n+1)
  for m in range(n+1):
    A[m] = Fr(1, m+1)
    for j in range(m, 0, -1):
      A[j-1] = j*(A[j-1] - A[j])
  return A[0].numerator*1./A[0].denominator # (which is Bn)


def VecToJac(vec):
  """ 
  Construction of the J matrix
  @param vec: a 3x1 vector for SO3 or a 6x1 vector for SE3 (input)
  @param J:   a 3x3 J matrix for SO3 or a 6x6 J matrix for SE3 (output)
  """
  tiny = 1e-12
  if vec.shape[0] == 3: # Jacobian of SO3
    phi = vec
    nr = np.linalg.norm(phi)
    if nr < tiny:
      # If the angle is small, fall back on the series representation
      JSO3 = VecToJacSeries(phi,10)
    else:
      axis = phi/nr
      cnr = np.cos(nr)
      snr = np.sin(nr)
      JSO3 = (snr/nr)*np.eye(3) + (1-snr/nr)*axis[np.newaxis]*axis[np.newaxis].T + ((1-cnr)/nr)*Hat(axis)
    return JSO3
  elif vec.shape[0] == 6: # Jacobian of SE3
    rho = vec[:3]
    phi = vec[3:]
    nr = np.linalg.norm(phi)
    if nr < tiny:
      #If the angle is small, fall back on the series representation
      JSE3 = VecToJacSeries(phi,10);
    else:
      JSO3 = VecToJac(phi)
      Q = VecToQ(vec)
      JSE3 = np.zeros((6,6))
      JSE3[:3,:3] = JSO3
      JSE3[:3,3:] = Q
      JSE3[3:,3:] = JSO3
    return JSE3
  else:
    raise ValueError("Invalid input vector length\n")


def VecToJacSeries(vec,N):
  """ 
  Construction of the J matrix from Taylor series
  @param vec: a 3x1 vector for SO3 or a 6x1 vector for SE3 (input)
  @param N:   number of terms to include in the series (input)
  @param J:   a 3x3 J matrix for SO3 or a 6x6 J matrix for SE3 (output)
  """
  if vec.shape[0] == 3: # Jacobian of SO3
    JSO3 = np.eye(3)
    pxn = np.eye(3)
    px = Hat(vec)
    for n in range(N):
      pxn = np.dot(pxn,px)/(n+2)
      JSO3 = JSO3 + pxn
    return JSO3
  elif vec.shape[0] == 6: # Jacobian of SE3
    JSE3 = np.eye(6)
    pxn = np.eye(6)
    px = CurlyHat(vec)
    for n in range(N):
      pxn = np.dot(pxn,px)/(n+2)
      JSE3 = JSE3 + pxn
    return JSE3
  else:
    raise ValueError("Invalid input vector length\n")
  return


def VecToQ(vec):
  """
  @param vec: a 6x1 vector (input)
  @param Q:   the 3x3 Q matrix (output)
  """
  rho = vec[:3]
  phi = vec[3:]
  
  nr = np.linalg.norm(phi)
  if nr == 0:
    nr = 1e-12
  nr2 = nr*nr
  nr3 = nr2*nr
  nr4 = nr3*nr
  nr5 = nr4*nr
  
  cnr = np.cos(nr)
  snr = np.sin(nr)
  
  rx = Hat(rho)
  px = Hat(phi)
  
  t1 = 0.5*rx
  t2 = ((nr-snr)/nr3)*(np.dot(px,rx) + np.dot(rx,px) + np.dot(np.dot(px,rx),px))
  m3 = (1-0.5*nr2 - cnr)/nr4
  t3 = -m3*(np.dot(np.dot(px,px),rx) +np.dot(np.dot(rx,px),px) -3*np.dot(np.dot(px,rx),px))
  m4 = 0.5*(m3 - 3*(nr - snr -nr3/6)/nr5)
  t4 = -m4*(np.dot(px,np.dot(np.dot(rx,px),px)) + np.dot(px,np.dot(np.dot(px,rx),px)))
  Q = t1 + t2 + t3 + t4
  return Q


def VecToTran(vec):
  """
  Build a transformation matrix using the exponential map, closed form
  @param vec: 6x1 vector (input)
  @param T:   4x4 transformation matrix (output)
  """
  rho = vec[:3]
  phi = vec[3:]
  
  C = VecToRot(phi)
  JSO3 = VecToJac(phi)
  
  T = np.eye(4)
  T[:3,:3] = C
  T[:3,3] = np.dot(JSO3,rho)
  return T


def VecToTranSeries(p, N):
  """
  Build a transformation matrix using the exponential map series with N elements in the series
  @param p: 6x1 vector (input)
  @param N: number of terms to include in the series (input)
  @param T: 4x4 transformation matrix (output)
  """
  T = np.eye(4)
  xM = np.eye(4)
  bpP = Hat(p)
  for n in range(N):
    xM = np.dot(xM, bpP/(n+1))
    T = T + xM
  return T

  
def Propagating(T1, sigma1, T2, sigma2, method = 2):
  """
  Find the total uncertainty in a compound spatial relation (Compounding two uncertain transformations)
  @param T1:     4x4 mean of left transformation 
  @param sigma1: 6x6 covariance of left transformation
  @param T2:     4x4 mean of right transformation
  @param sigma2: 6x6 covariance of right transformations
  @param method: an integer indicating the method to be used to perform compounding
                 (1=second-order, 2=fourth-order)
  @param T:      4x4 mean of compounded transformation (output)
  @param sigma:  6x6 covariance of compounded transformation (output)
  """
  # Compound the means
  T = np.dot(T1,T2)
  # Compute Adjoint of transformation T1
  AdT1 = TranAd(T1)
  sigma2prime = np.dot(np.dot(AdT1,sigma2),AdT1)
  if method == 1:
    # Second-order method
    sigma = sigma1 + sigma2prime    
  elif method == 2:
    # Fourth-order method
    sigma1rr = sigma1[:3,:3]
    sigma1rp = sigma1[:3,3:]
    sigma1pp = sigma1[3:,3:]
    
    sigma2rr = sigma2prime[:3,:3]
    sigma2rp = sigma2prime[:3,3:]
    sigma2pp = sigma2prime[3:,3:]
    
    A1 = np.zeros((6,6))
    A1[:3,:3] = CovOp1(sigma1pp)
    A1[:3,3:] = CovOp1(sigma1rp + sigma1rp.T)
    A1[3:,3:] = CovOp1(sigma1pp)
    
    A2 = np.zeros((6,6))
    A2[:3,:3] = CovOp1(sigma2pp)
    A2[:3,3:] = CovOp1(sigma2rp + sigma2rp.T)
    A2[3:,3:] = CovOp1(sigma2pp)

    Brr = CovOp2(sigma1pp,sigma2rr) + CovOp2(sigma1rp.T,sigma2rp) + CovOp2(sigma1rp,sigma2rp.T) + CovOp2(sigma1rr,sigma2pp)
    Brp = CovOp2(sigma1pp,sigma2rp.T) + CovOp2(sigma1rp.T,sigma2pp)
    Bpp = CovOp2(sigma1pp, sigma2pp)
    
    B = np.zeros((6,6))
    B[:3,:3] = Brr
    B[:3,3:] = Brp
    B[3:,:3] = Brp.T
    B[3:,3:] = Bpp
    
    sigma = sigma1 + sigma2prime + 1/12.*(np.dot(A1,sigma2prime)+np.dot(sigma2prime,A1.T) + np.dot(sigma1,A2) + np.dot(sigma1,A2.T)) + B/4.   
  return T, sigma


def Fusing(Tlist, sigmalist, N = 0):
  """
  Find the total uncertainty in a compound spatial relation (Compounding two uncertain transformations)
  @param Tlist:     a list of 4x4 transformations
  @param sigmalist: a list of corresponding 6x6 covariance matrices
  @param N:         N == 0(default):JacInv is computed analytically using eq. 100
                    N != 0: JacInv is computed using eq. 103, using N first terms in the eq.
  @param T:      4x4 mean of fused transformation (output)
  @param sigma:  6x6 covariance of fused transformation (output)
  """
  assert len(Tlist) == len(sigmalist), "Invalid data list length\n"
  kmax = len(Tlist)
  
  T = Tlist[0]
  Vprv = 0
  for i in range(30): # Gauss-Newton iterations
    LHS = np.zeros(6)
    RHS = np.zeros(6)
    for k in range(kmax):
      xik = TranToVec(np.dot(T,np.linalg.inv(Tlist[k])))
      if N ==0:
        invJ = VecToJacInv(xik)
      else:
        invJ = VecToJacInvSeries(xik, N)
      invJtS = np.dot(invJ.T, np.linalg.inv(sigmalist[k]))
      LHS = LHS + np.dot(invJtS,invJ)
      RHS = RHS + np.dot(invJtS, xik)
    
    xi = -np.linalg.solve(LHS,RHS)
    print "xi", xi
    T = np.dot(VecToTran(xi),T)
    print "T", T
    sigma = np.linalg.inv(LHS)
    
    # How low did the objective function get?
    V = 0
    for k in range(kmax):
      xik = TranToVec(np.dot(T,np.linalg.inv(Tlist[k])))
      V = V + np.dot(np.dot(xik.T,np.linalg.inv(sigmalist[k])),xik)/2

    if abs(V - Vprv) < 1e-10:
      return T, sigma 
    Vprv = V
  return T, sigma
 
     
def Visualize(Tlist,sigmalist, nsamples = 100):
  """
  Visualize an estimation (a point will be used to represent the translation position of a transformation)
  @param Tlist:     a list of Transformations
  @param sigmalist: a list of corresponding sigmas
  @param nsamples:  the number of samples generated for each (T,sigma)
  """
  import matplotlib.cm as cm
  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')
  cholsigmalist = []
  colors = iter(cm.rainbow(np.linspace(0, 1, len(Tlist))))
  for i in range(len(sigmalist)):
    color = next(colors)
    cholsigma = np.linalg.cholesky(sigmalist[i]).T
    Tsample = []
    for k in range(nsamples):
      vecsample = np.dot(cholsigma,np.random.randn(6,1))
      #vecsample = np.dot(cholsigma, np.random.uniform(-1,1,size = 6))
      vecsample.resize(6)
      Tsample = np.dot(VecToTran(vecsample), Tlist[i])
      ax.scatter(Tsample[0,3],Tsample[1,3],Tsample[2,3], c = color)

  ax.set_autoscaley_on(False)
  ax.set_xlim([-0.5, 0.5])
  ax.set_ylim([-0.5, 0.5])
  ax.set_zlim([-0.5, 0.5])
  ax.set_xlabel('X Label')
  ax.set_ylabel('Y Label')
  ax.set_zlabel('Z Label')
  plt.show(False)
  return True


def IsInside(point, center, sigma):
  """
  Check whether a point (transformation) is in the region formed by (center,sigma) or not 
  """
  cholsigma = np.linalg.cholesky(sigma).T
  univariable = np.dot(np.linalg.inv(cholsigma),(point-center))
  nr = np.linalg.norm(univariable)
  if nr <= 1.0:
    return True
  else:
    return False