import pyfits as py,numpy as np,pylab as pl
import veltools as T
import special_functions as sf
from fittertest import finddispersion,readresults
from scipy import ndimage,signal,interpolate
from math import sqrt,log10,log
import ndinterp
from tools import iCornerPlotter, gus_plotting as g

dir = '/data/ljo31b/EELs/esi/INDOUS/'
templates = ['102328_K3III.fits','163588_K2III.fits','107950_G5III.fits','124897_K1III.fits','168723_K0III.fits','111812_G0III.fits','148387_G8III.fits','188350_A0III.fits','115604_F2III.fits']

for i in range(len(templates)):
    templates[i] = dir+templates[i]

twave  = np.log10(T.wavelength(templates[0],0))
tscale = twave[1]-twave[0]

VGRID = 1.
light = 299792.458
ln10 = np.log(10.)

# science data resolution, template resolution
sigtmp1 =  0.44/7000. * light
sigtmp2 = light/500.



def getmodel(twave,tspec,tscale,smin=5.,smax=501):
    match = tspec.copy()
    disps = np.arange(smin,smax,VGRID)
    cube = np.empty((disps.size,twave.size))
    #dispkerns = disps*0.
    for i in range(disps.size):
        disp = disps[i]
        dispkern = (disp**2.+sigsci**2.-sigtmp1**2.)**0.5
        if np.isnan(dispkern)==True:
            dispkern = 5.
        #print disp,dispkern
        kernel = dispkern/(light*ln10*tscale)
        cube[i] = ndimage.gaussian_filter1d(match.copy(),kernel)
        #dispkerns[i] = dispkern
    '''pl.figure()
    pl.hist(disps,30)
    pl.hist(dispkerns,30)
    pl.show()
    pl.figure()
    pl.scatter(disps,dispkerns)
    pl.show()'''
    X = disps.tolist()
    tx = np.array([X[0]]+X+[X[-1]])
    Y = twave.tolist()
    ty = np.array([Y[0]]+Y+[Y[-1]])
    return  (tx,ty,cube.flatten(),1,1)

def run(zl,zs,fit=True,read=False,File=None,mask=None,lim=6000.,nfit=6.,bg='polynomial',bias=1e8):
    # Load in spectrum
    sciwave,scispec,varspec = np.load('/data/ljo31b/EELs/esi/testcode/summedspec_neu.npy')
    #varspec = varspec**-2.
    #sciwave -= np.log10(1.111974/1.3)
    print 'bias',np.log10(bias)

    # cut nonsense data - nans at edges
    edges = np.where(np.isnan(scispec)==False)[0]
    start = edges[0]
    end = sciwave.size
    #end = np.where(sciwave>np.log10(10000.))[0][0]
    scispec = scispec[start:end]
    varspec = varspec[start:end]
    datascale = sciwave[1]-sciwave[0] # 1.7e-5
    sciwave = 10**sciwave[start:end]
    
    zp = scispec.mean()
    scispec /= zp
    varspec /= zp**2

    # prepare the templates
    ntemps = len(templates)
    ntemp = 1
    result = []
    models = []
    t = []

    tmin = sciwave.min()
    tmax = sciwave.max()

    for template in templates:
        # Load the template
        file = py.open(template)
        tmpspec = file[0].data.astype(np.float64)
        tmpwave = T.wavelength(template,0)
        tmpspec /= tmpspec.mean()

        # do we need to smooth these? Presumably not, because our resolution is better
        twave = np.log10(tmpwave)
        tmpscale = twave[1]-twave[0]
        t.append(getmodel(twave,tmpspec,tmpscale)) 
    np.save('/data/ljo31b/EELs/esi/testcode/testtemplates2',t)
    np.save('/data/ljo31b/EELs/esi/testcode/testtwave2',tmpwave)
        #pl.figure()
        #pl.plot(tmpwave,tmpspec)
        #pl.show()
    if fit:
        result = finddispersion(scispec,varspec,t,tmpwave,np.log10(sciwave),zl,zs,nfit=nfit,outfile=File,mask=mask,lim=lim,bg=bg,bias=bias)
        return result
    elif read:
        result = readresults(scispec,varspec,t,tmpwave,np.log10(sciwave),zl,zs,nfit=nfit,infile=File,mask=mask,lim=lim,bg=bg,bias=bias)
        return result
    else:
        return


name='testcodehitrueres2'#_hires'
# get resolution: spec has an extension for this
lenspec = py.open('/data/ljo31b/EELs/esi/testcode/spec-2157-54242-0324.fits')
sourcespec = py.open('/data/ljo31b/EELs/esi/testcode/spec-1653-53534-0550.fits')
wdisp1, wdisp2 = lenspec[1].data['wdisp'].mean(), sourcespec[1].data['wdisp'].mean()
sig = np.mean((wdisp1,wdisp2))
sig *= 0.0001*np.log(10.) # 0.0001 = cd1_1, dispersion of each pixel; fixed at 69 km/s = 0.0001 * ln(10) * c
sigsci = sig * light
# nb. 'Since sdss spectra are binned with constant logarithmic dispersion, the pixel size is fixed in velocity space at 69 km/s = ln(10) * c * 0.0001, where 0.0001 is the log-base-10 dispersion per pixel (stored in the header field cd1_1). To convert to resolution in wavelength units, multiply by the local pixel size in wavelength units, which is ln(10) * lambda * 0.0001 where lambda is the wavelength of the pixel and 0.0001 is again the log 10 dispersion.


# nb. true sigmas: sigma lens = 229.57, sigma src = 272.33

result = run(0.111974,0.311078,fit=True,read=False,File = name,mask=np.array([[5560,5620],[6300,6320],[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4800.,bias=1e9)
result = run(0.111974,0.311078,fit=False,read=True,File = name,mask=np.array([[5560,5620],[6300,6320],[7580,7700],[6860,6900]]),nfit=6,bg='polynomial',lim=4800.,bias=1e9)
pl.title('fake SDSS EEL')
pl.xlim([4800,9000])
pl.show()

'''result = run(0.3,0.5327701,fit=True,read=False,File = name,mask=np.array([[5560,5620],[6300,6320],[7580,7700],[6860,6900]])*(1.3/1.111974),nfit=6,bg='polynomial',lim=5650.,bias=1e12)
result = run(0.3,0.5327701,fit=False,read=True,File = name,mask=np.array([[5560,5620],[6300,6320],[7580,7700],[6860,6900]])*(1.3/1.111974),nfit=6,bg='polynomial',lim=5650.,bias=1e12)
pl.title(name)
pl.xlim([4000,10000])
pl.show()
'''
result = np.load('/data/ljo31b/EELs/esi/kinematics/trials/testcodehitrueres2')
lp,trace,dic,_ = result
velL,sigL,velS,sigS = np.median(trace[300:,:].reshape(((trace.shape[0]-300)*trace.shape[1],trace.shape[2])),axis=0)
print velL, sigL, velS, sigS

# uncertainties
f = trace[300:,:].reshape(((trace.shape[0]-300)*trace.shape[1],trace.shape[2]))
velLlo, sigLlo,velSlo,sigSlo = np.percentile(f,16,axis=0)
velLhi,sigLhi,velShi,sigShi = np.percentile(f,84,axis=0)

print 'lens velocity', '%.2f'%velL, '\pm', '%.2f'%(velL-velLlo)
print 'lens dispersion', '%.2f'%sigL, '\pm', '%.2f'%(sigL-sigLlo)
print 'source velocity', '%.2f'%velS, '\pm', '%.2f'%(velS-velSlo)
print 'source dispersion', '%.2f'%sigS, '\pm', '%.2f'%(sigS-sigSlo)

pl.figure()
pl.subplot(221)
key = 'lens velocity'
pl.hist(dic[key][300:].ravel(),30,histtype='stepfilled')
pl.title(key)
pl.subplot(222)
key = 'lens dispersion'
pl.hist(dic[key][300:].ravel(),30,histtype='stepfilled')
pl.title(key)
pl.axvline(229.57,color='k')
pl.subplot(223)
key = 'source velocity'
pl.hist(dic[key][300:].ravel(),30,histtype='stepfilled')
pl.title(key)
pl.subplot(224)
key = 'source dispersion'
pl.hist(dic[key][300:].ravel(),30,histtype='stepfilled')
pl.title(key)
pl.axvline(272.33,color='k')
pl.show()

'''from tools import gus_plotting as g
chain = g.changechain(trace,filename='test')
g.triangle_plot(chain,burnin=300,truevals=[0,229.57,0,272.33])
pl.show()'''
