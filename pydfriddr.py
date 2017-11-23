"""
This is an example on how to test the quality of MESA's derivatives using ridders method of polynomial extrapolation.

By defining a function in eval_x and eval_dx we can test how mesa derivatives handle changes in the x value. This
is already done in MESA in star/private/star_newton.f90 but its tightly coupled to the solver.
This way we can test the derivatives from the low level modules without needing to have a whole star setup.

It does mean though we can not test the compound derivatives inside hydro_eqns.

"""

import pyMesaUtils as pym
import numpy as np

neu_lib,neu_def = pym.loadMod("neu")

def eval_x(x):
    """
    This should take the x value being tested and return y(x)
    
    """
    
    T=x
    log10_T=np.log10(T)
    
    Rho=10**9.0
    log10_Rho=np.log10(T)
    abar=1.0
    zbar=1.0
    z2bar=1.0
    log10_Tlim=7.5
    flags=np.zeros(neu_def.num_neu_types.get())
    flags[:]=True
    info=0
    
    index=neu_def.ineu.get()-1
    
    
    num_neu_rvs=neu_def.num_neu_rvs.get()
    num_neu_types=neu_def.num_neu_types.get()
    loss=np.zeros(num_neu_rvs)
    sources=np.zeros((num_neu_types,num_neu_rvs))
    
    res = neu_lib.neu_get(T, log10_T, Rho, log10_Rho, abar, zbar, z2bar, log10_Tlim, flags, loss, sources, info)
    
    return res['loss'][index]
    
def eval_dx(x):
    """
    This should take the x value being tested and return dy/dx at x
    
    """
    
    T=x
    log10_T=np.log10(T)
    
    Rho=10**9.0
    log10_Rho=np.log10(T)
    abar=1.0
    zbar=1.0
    z2bar=1.0
    log10_Tlim=7.5
    flags=np.zeros(neu_def.num_neu_types.get())
    flags[:]=True
    info=0
    
    index=neu_def.idneu_dT.get()-1
    
    num_neu_rvs=neu_def.num_neu_rvs.get()
    num_neu_types=neu_def.num_neu_types.get()
    loss=np.zeros(num_neu_rvs)
    sources=np.zeros((num_neu_types,num_neu_rvs))
    
    res = neu_lib.neu_get(T, log10_T, Rho, log10_Rho, abar, zbar, z2bar, log10_Tlim, flags, loss, sources, info)
    
    return res['loss'][index]



def eval_func(start_x,start_step,func=eval_x,func_dx=eval_dx):
    """
    Evaluate a function and its derivative by using ridders method of polynomial extrapolation
    Coded taken from $MESA_DIR/star/private/star_newton.f90 dfridr function
    
    Inputs:
    start_x: Float, Point we wish to test
    start_step: Float, Starting step over which the function changes substantially
    func: Function, Function that takes as argument the start_x and returns y(start_x) being tested
    func_dx: Function, Function that takes as argument the start_x and returns the dy/dx at start_x
    
    Returns:
    None
    
    """
    
    ntab=20+1 # Use fortran numbering and start at 1
    con2=2.0
    con=con2**0.5
    err=10**50
    safe=2.0
    
    a=np.zeros((ntab,ntab))
    step=start_step
    a[1,1] = (func(start_x+step) - func(start_x-step)) / (2.0*step) 
    print('\tdfdx',1,a[1,1],start_step)
    for i in range(2,ntab+1):
        step=step/con
        a[1,i]=(func(start_x+step) - func(start_x-step)) / (2.0*step)
        print('\tdfdx',i,a[1,i],step)
        fac=con2
        for j in range(2,i+1):
            a[j,i]=(a[j-1,i]*fac - a[j-1,i-1])/(fac-1.0)
            fac=con2*fac
            errt=np.maximum(np.abs(a[j,i]-a[j-1,i]),np.abs(a[j,i]-a[j-1,i-1]))
            if errt < err:
                err=errt
                dfridr = a[j,i]
                print('\t\tdfridr err',i,j,dfridr,err)
        if np.abs(a[i,i] - a[i-1,i-1]) >= safe*err:
            print("Higher order is worse")
            break
        
    dvardx_0 = func_dx(start_x)
    xdum=(dfridr-dvardx_0)/(np.maximum(dvardx_0,10**-50))
    print()
    print('analytic numeric err rel_diff',dvardx_0,dfridr,err,xdum)
    

eval_func(10**9,10**8,eval_x)
