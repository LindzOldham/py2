import pyfits as py,numpy as np,pylab as pl
import veltools as T
import special_functions as sf
from stitchfitter2 import finddispersion,readresults
from scipy import ndimage,signal,interpolate
from math import sqrt,log10,log
import ndinterp
from tools import iCornerPlotter, gus_plotting as g


dir = '/data/ljo31b/EELs/esi/INDOUS/' 
templates1 = ['102328_K3III.fits','163588_K2III.fits','107950_G5III.fits','124897_K1III.fits','168723_K0III.fits','111812_G0III.fits','148387_G8III.fits','188350_A0III.fits','115604_F2III.fits']

for i in range(len(templates1)):
    templates1[i] = dir+templates1[i]

dir = '/data/ljo31b/EELs/esi/PICKLES/'
templates2 = ['K3III.dat','K2III.dat','G5III.dat','K1III.dat','K0III.dat','G0III.dat','G8III.dat','A0III.dat','F2III.dat']

for i in range(len(templates2)):
    templates2[i] = dir+templates2[i]

VGRID = 1.
light = 299792.458
ln10 = np.log(10.)

# science data resolution, template resolution - all esi spectra have virtually the same resolution, but may as well measure them separately!
sigtmp1 =  0.44/7000. * light
sigtmp2 = light/500.

def getmodel(twave,tspec,tscale,sigsci,sigtmp,smin=5.,smax=501):
    match = tspec.copy()
    disps = np.arange(smin,smax,VGRID)
    cube = np.empty((disps.size,twave.size))
    for i in range(disps.size):
        disp = disps[i]
        dispkern = (disp**2.+sigsci**2.-sigtmp**2.)**0.5
        if np.isnan(dispkern)==True:
            dispkern = 5. 
        kernel = dispkern/(light*ln10*tscale)
        cube[i] = ndimage.gaussian_filter1d(match.copy(),kernel)
    X = disps.tolist()
    tx = np.array([X[0]]+X+[X[-1]])
    Y = twave.tolist()
    ty = np.array([Y[0]]+Y+[Y[-1]])
    return  (tx,ty,cube.flatten(),1,1)


def run(zl,zs,fit=True,read=False,File=None,mask=None,lim=5000.,nfit=6.,bg='polynomial',bias=1e8,restmask=None,srclim=6000.,lenslim=5500.):
    # Load in spectrum
    scispec = py.open('/data/ljo31b/EELs/esi/kinematics/'+name[:5]+'_spec.fits')[0].data
    varspec = py.open('/data/ljo31b/EELs/esi/kinematics/'+name[:5]+'_var.fits')[0].data
    sciwave = py.open('/data/ljo31b/EELs/esi/kinematics/'+name[:5]+'_wl.fits')[0].data
    
    # cut nonsense data - nans at edges
    edges = np.where(np.isnan(scispec)==False)[0]
    start = edges[0]
    end = np.where(sciwave>np.log10(9000.))[0][0] # changed from 9500!
    scispec = scispec[start:end]
    varspec = varspec[start:end]
    datascale = sciwave[1]-sciwave[0] # 1.7e-5
    sciwave = 10**sciwave[start:end]

    zp = scispec.mean()
    scispec /= zp
    varspec /= zp**2

    # prepare the templates
    ntemps1 = len(templates1)
    ntemps2 = len(templates2)

    result = []
    models = []
    t1,t2 = [],[]
    
    for template in templates1:
        file = py.open(template)
        tmpspec1 = file[0].data.astype(np.float64)
        tmpwave1 = T.wavelength(template,0)
        tmpspec1 /= tmpspec1.mean()

        twave1 = np.log10(tmpwave1)
        tmpscale1 = twave1[1]-twave1[0]
        t1.append(getmodel(twave1,tmpspec1,tmpscale1,sigsci,sigtmp1)) 
    
    for template in templates2:
        tmpwave2,tmpspec2 = np.loadtxt(template,unpack=True)
        tmpwave2 *= 10.
        tmpspec2 /= tmpspec2.mean()

        twave2 = np.log10(tmpwave2)
        tmpscale2 = twave2[1]-twave2[0]
        t2.append(getmodel(twave2,tmpspec2,tmpscale2,sigsci,sigtmp2)) 

    ntemps1,ntemps2 = len(t1), len(t2)

    if fit:
        result = finddispersion(scispec,varspec,t1,t2,tmpwave1,tmpwave2,np.log10(sciwave),zl,zs,nfit=nfit,outfile=File,mask=mask,lim=lim,bg=bg,restmask=restmask,srclim=srclim,lenslim=lenslim)
        return result
    elif read:
        result = readresults(scispec,varspec,t1,t2,tmpwave1,tmpwave2,np.log10(sciwave),zl,zs,nfit=nfit,infile=File,mask=mask,lim=lim,bg=bg,restmask=restmask,srclim=srclim,lenslim=lenslim)
        return result
    else:
        return

sz = np.load('/data/ljo31/Lens/LensParams/SourceRedshifts.npy')[()]
lz = np.load('/data/ljo31/Lens/LensParams/LensRedshifts.npy')[()]
resolutions = np.load('/data/ljo31b/EELs/esi/spectra/resolutions_from_skylines_may2014.npy')[()]

import sys
name = sys.argv[1]
print name
triangle=False

if name=='J1248':
    name='J1248_stitch2'
    sigsci = resolutions[name[:5]] * light
    print sigsci

    result = run(lz[name[:5]],sz[name[:5]],fit=True,read=False,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4500.,bias=1e8,srclim=5750.,lenslim=4900.)
    result = run(lz[name[:5]],sz[name[:5]],fit=False,read=True,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4500.,bias=1e8,srclim=5750.,lenslim=4900.)
    pl.title(name[:5])
    pl.savefig('/data/ljo31b/EELs/esi/kinematics/plots/'+name[:5]+'.pdf')

elif name == 'J1323':
    name = 'J1323_stitch_2'
    sigsci = resolutions[name[:5]] * light

    result = run(lz[name[:5]],sz[name[:5]],fit=True,read=False,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e8,srclim=5500.,lenslim=4900.)
    result = run(lz[name[:5]],sz[name[:5]],fit=False,read=True,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e8,srclim=5500.,lenslim=4900.)
    pl.title(name[:5])
    pl.savefig('/data/ljo31b/EELs/esi/kinematics/plots/'+name[:5]+'.pdf')
    pl.show()

elif name == 'J1347':
    name = 'J1347_stitch_2'
    sigsci = resolutions[name[:5]] * light
   
    result = run(lz[name[:5]],sz[name[:5]],fit=True,read=False,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e9,srclim=6000.,lenslim=5200.)
    result = run(lz[name[:5]],sz[name[:5]],fit=False,read=True,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e9,srclim=6000.,lenslim=5200.)
    pl.title(name[:5])
    pl.savefig('/data/ljo31b/EELs/esi/kinematics/plots/'+name[:5]+'.pdf')
    pl.show()

elif name == 'J1446':
    name = 'J1446_stitch_2bias'
    sigsci = resolutions[name[:5]] * light
    
    result = run(lz[name[:5]],sz[name[:5]],fit=True,read=False,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e9,srclim=5800.,lenslim=4850.)
    result = run(lz[name[:5]],sz[name[:5]],fit=False,read=True,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e9,srclim=5800.,lenslim=4850.)
    pl.title(name[:5])
    pl.savefig('/data/ljo31b/EELs/esi/kinematics/plots/'+name[:5]+'.pdf')
    pl.show()

elif name == 'J1605':
    name = 'J1605_stitch_2'
    sigsci = resolutions[name[:5]] * light
    
    result = run(lz[name[:5]],sz[name[:5]],fit=True,read=False,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e8,srclim=5700.,lenslim=4850.)
    result = run(lz[name[:5]],sz[name[:5]],fit=False,read=True,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e8,srclim=5700.,lenslim=4850.)
    pl.title(name[:5])
    pl.savefig('/data/ljo31b/EELs/esi/kinematics/plots/'+name[:5]+'.pdf')
    pl.show()

elif name == 'J1606':
    name = 'J1606_stitch_2'
    sigsci = resolutions[name[:5]] * light
    
    result = run(lz[name[:5]],sz[name[:5]],fit=True,read=False,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e8,srclim=6100.,lenslim=5100.)
    result = run(lz[name[:5]],sz[name[:5]],fit=False,read=True,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e8,srclim=6100.,lenslim=5100.)
    pl.title(name[:5])
    pl.savefig('/data/ljo31b/EELs/esi/kinematics/plots/'+name[:5]+'.pdf')
    pl.show()

elif name == 'J1619':
    name = 'J1619_stitch_2'
    sigsci = resolutions[name[:5]] * light
    
    result = run(lz[name[:5]],sz[name[:5]],fit=True,read=False,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e8,srclim=5900.,lenslim=5000.)
    result = run(lz[name[:5]],sz[name[:5]],fit=False,read=True,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4750.,bias=1e8,srclim=5900.,lenslim=5000.)
    pl.title(name[:5])
    pl.savefig('/data/ljo31b/EELs/esi/kinematics/plots/'+name[:5]+'.pdf')
    pl.show()

elif name == 'J2228':
    name = 'J2228_stitch_2_test'
    sigsci = resolutions[name[:5]] * light
    
    result = run(lz[name[:5]],sz[name[:5]],fit=True,read=False,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4550.,bias=1e8,srclim=5300.,lenslim=4600.)
    result = run(lz[name[:5]],sz[name[:5]],fit=False,read=True,File = name,mask=np.array([[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4550.,bias=1e8,srclim=5300.,lenslim=4600.)
    pl.title(name[:5])
    pl.savefig('/data/ljo31b/EELs/esi/kinematics/plots/'+name[:5]+'.pdf')
    pl.show()

if triangle:
    lp,trace,dic,_ = result
    chain = g.changechain(trace,filename='/data/ljo31b/EELs/esi/kinematics/inference/'+name+'_chain')
    np.savetxt('/data/ljo31b/EELs/esi/kinematics/inference/'+name+'_chain.txt',chain[6000:,1:])
    g.triangle_plot(chain,burnin=125,axis_labels=['$v_l$',r'$\sigma_l$','$v_s$',r'$\sigma_s$'])
    pl.show()



'''
to print results:
result = np.load('/data/ljo31b/EELs/esi/kinematics/inference/J0901')
zl=lzs['J0901']
zs=szs['J0901']

lp,trace,dic,_ = result
medians = []
diffs = []

for key in dic.keys():
    f = dic[key][150:,:]                                          
    f = f.flatten()
    l,m,u = np.percentile(f,16,axis=0),np.percentile(f,50,axis=0),np.percentile(f,84,axis=0)
    med, dmed = m, np.mean((m-l,u-m))
    medians.append(med)
    diffs.append(dmed)

for i in range(len(dic.keys())):
    print dic.keys()[i], '%.2f'%medians[i], '\pm', '%.2f'%diffs[i]

# update redshifts
print zl+medians[0]/light
print zs+medians[-1]/light

'''
