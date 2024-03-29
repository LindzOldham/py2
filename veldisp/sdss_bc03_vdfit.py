import pyfits as py,numpy as np,pylab as pl
import veltools as T
import special_functions as sf
from stitchfitter_sdss_vdfit import finddispersion,readresults
from scipy import ndimage,signal,interpolate
from math import sqrt,log10,log
import ndinterp
from tools import iCornerPlotter, gus_plotting as g
from scipy import sparse
from scipy.interpolate import splrep, splev
import VDfit

import sys
name,nthreads = sys.argv[1],int(sys.argv[2])
print name

dir = '/data/ljo31b/EELs/sdss/'
sz = np.load('/data/ljo31/Lens/LensParams/SourceRedshiftsUpdated.npy')[()]
lz = np.load('/data/ljo31/Lens/LensParams/LensRedshiftsUpdated.npy')[()]
filename=name+'_sdss_bc03_vdfit'


def run(zl,zs,fit=True,read=False,File=None,mask=np.array([[5570,5585],[7580,7700],[6860,6900]]),nfit=10.,bg='polynomial',bias=10,restmask=None):
    # Load in spectrum
    spec = py.open(dir+name+'.fits')[1].data
    sciwave = spec['loglam']
    scispec = spec['flux']
    varspec = spec['ivar']**-1.
    wdisp = spec['wdisp']
    wdispmod = splrep(10**sciwave,wdisp,k=1)
    
    def sigsci(wave):
        return splev(wave,wdispmod)*0.0001*np.log(10.)*299792.458

    t1 = VDfit.BC03(sigsci)
    t2 = VDfit.PICKLES(sigsci)

    # define region of interest
    if type(zl)!=float:#>1.:
        zl,zs = zl[0],zs[0]
    print zl, zs
    lim = 3800.*(1.+zl)
    maxlim = 4800.*(1.+zs)
    srclim = 3320.*(1.+zs)+40.
    #if name == 'J1125':
    #    maxlim = 7880.
    if srclim<=lim:
        srclim = lim+10.
    print 'lims: ', lim,srclim, maxlim

    # cut nonsense data - nans at edges
    edges = np.where(np.isnan(scispec)==False)[0]
    start = edges[0]
    end = np.where(sciwave>np.log10(maxlim))[0][0]
    scispec = scispec[start:end]
    varspec = varspec[start:end]
    datascale = sciwave[1]-sciwave[0] # 1.7e-5
    sciwave = 10**sciwave[start:end]

    zp = scispec.mean()
    scispec /= zp
    varspec /= zp**2

    if fit:
        print 'running on ', nthreads, ' threads'
        #result = finddispersion(scispec,varspec,t1,t2,np.log10(sciwave),zl,zs,nfit=10,outfile=File,mask=mask,lim=lim,bg=bg,restmask=restmask,srclim=srclim,maxlim=maxlim,bias=bias,nthr=nthreads,name=name)
        return #result
    elif read:
        result = readresults(scispec,varspec,t1,t2,np.log10(sciwave),zl,zs,nfit=10,infile=File,mask=mask,lim=lim,bg=bg,restmask=restmask,srclim=srclim,maxlim=maxlim,bias=bias)
        return result
    else:
        return


if name=='J0837':
    #result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    

elif name == 'J0901':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    

elif name == 'J0913':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    

elif name == 'J1125':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    

elif name == 'J1144':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    

elif name == 'J1218':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename) 
    result = run(lz[name],sz[name],fit=False,read=True,File = filename) 
    
# may 2014 dataset

elif name == 'J1323':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    

elif name == 'J1347':
    #result = run(lz[name],sz[name],fit=True,read=False,File = filename,bias=30)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename,bias=30)
    

elif name == 'J1446':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)


elif name == 'J1605':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    

elif name == 'J1606':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    

elif name == 'J1619':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename,bias=30)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename,bias=30)


elif name == 'J2228':
    result = run(lz[name],sz[name],fit=True,read=False,File = filename)
    result = run(lz[name],sz[name],fit=False,read=True,File = filename)
    


lp,trace,dic,_=result
#np.savetxt('/data/ljo31b/EELs/esi/kinematics/inference/vdfit/'+filename+'_chain.dat',trace[200:].reshape((trace[200:].shape[0]*trace.shape[1],trace.shape[-1])),header=' lens velocity -- lens dispersion -- source velocity -- source dispersion \n -500,500, 0,500, -500,500, 0,500')
pl.show()
#pl.suptitle(name)
#pl.savefig('/data/ljo31b/EELs/esi/kinematics/inference/plots/'+filename+'.pdf')
#pl.savefig('/data/ljo31/public_html/Lens/sdss_eels_spectra/texplots/fits_sdss_bc03/'+filename+'.png')
#pl.figure()
#pl.plot(lp)
#pl.show()

#from tools import iCornerPlotter as i
#i.CornerPlotter(['/data/ljo31b/EELs/esi/kinematics/inference/'+filename+'_chain.dat,blue'])
#pl.show()
