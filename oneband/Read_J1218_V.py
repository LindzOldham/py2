import cPickle,numpy,pyfits as py
import pymc
from pylens import *
from imageSim import SBModels,convolve,SBObjects
import indexTricks as iT
from SampleOpt import AMAOpt
import pylab as pl
import numpy as np
import myEmcee_blobs as myEmcee
from matplotlib.colors import LogNorm
from scipy import optimize
from scipy.interpolate import RectBivariateSpline
import SBBModels, SBBProfiles

# plot things
def NotPlicely(image,im,sigma):
    ext = [0,image.shape[0],0,image.shape[1]]
    #vmin,vmax = numpy.amin(image), numpy.amax(image)
    pl.figure()
    pl.subplot(221)
    pl.imshow(image,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto',vmin=0)#,vmax=4.5) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('data')
    pl.subplot(222)
    pl.imshow(im,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto',vmin=0)#,vmax=4.5) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('model')
    pl.subplot(223)
    pl.imshow(image-im,origin='lower',interpolation='nearest',extent=ext,vmin=-0.25,vmax=0.25,cmap='afmhot',aspect='auto')
    pl.colorbar()
    pl.title('data-model')
    pl.subplot(224)
    pl.imshow((image-im)/sigma,origin='lower',interpolation='nearest',extent=ext,vmin=-1,vmax=1,cmap='afmhot',aspect='auto')
    pl.title('signal-to-noise residuals')
    pl.colorbar()

def SotPleparately(image,im,sigma,col):
    ext = [0,image.shape[0],0,image.shape[1]]
    pl.figure()
    pl.imshow(image,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',vmin=0,aspect='auto') #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('data - '+str(col))
    pl.figure()
    pl.imshow(im,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',vmin=0,aspect='auto') #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('model - '+str(col))
    pl.figure()
    pl.imshow((image-im)/sigma,origin='lower',interpolation='nearest',extent=ext,vmin=-2,vmax=2,cmap='afmhot',aspect='auto')
    pl.title('signal-to-noise residuals - '+str(col))
    pl.colorbar()


img1 = py.open('/data/ljo31/Lens/J1218/F606W_sci_cutout.fits')[0].data.copy()[10:-10,10:-10]
sig1 = py.open('/data/ljo31/Lens/J1218/F606W_noisemap.fits')[0].data.copy()[10:-10,10:-10]
psf1 = py.open('/data/ljo31/Lens/J1218/F606W_psf1.fits')[0].data.copy()
psf1 = psf1/np.sum(psf1)
img2 = py.open('/data/ljo31/Lens/J1218/F814W_sci_cutout.fits')[0].data.copy()[10:-10,10:-10]
sig2 = py.open('/data/ljo31/Lens/J1218/F814W_noisemap.fits')[0].data.copy()[10:-10,10:-10]
psf2 = py.open('/data/ljo31/Lens/J1218/F814W_psf1.fits')[0].data.copy()
psf2 = psf2/np.sum(psf2)
Dx,Dy = -50.,-50.

result = np.load('/data/ljo31/Lens/LensModels/J1218_211')
lp= result[0]
a2=0
a1,a3 = numpy.unravel_index(lp[:,0].argmax(),lp[:,0].shape)
trace = result[1]
dic = result[2]

image,sigma,psf = img2,sig2,psf2
image,sigma,psf = img1,sig1,psf1
psf /= psf.sum()
psf = convolve.convolve(image,psf)[1]
PSF = psf

OVRS = 1
yc,xc = iT.overSample(image.shape,OVRS)
yo,xo = iT.overSample(image.shape,1)
xc,xo,yc,yo = xc+Dx , xo+Dx, yc+Dy, yo+Dy
mask = np.zeros(image.shape)
tck = RectBivariateSpline(yo[:,0],xo[0],mask)
mask2 = tck.ev(xc,yc)
mask2[mask2<0.5] = 0
mask2[mask2>0.5] = 1
mask2 = mask2==0
mask = mask==0

kresult = np.load('/data/ljo31/Lens/J1218/V_0')
klp= kresult[0]
ka2=0
ka1,ka3 = numpy.unravel_index(klp[:,0].argmax(),klp[:,0].shape)
ktrace = kresult[1]
kdic = kresult[2]

gals = []
for name in ['Galaxy 1', 'Galaxy 2']:
    p = {}
    if name == 'Galaxy 1':
        for key in 'x','y','q','pa','re','n':
            p[key] = dic[name+' '+key][a1,a2,a3]
    elif name == 'Galaxy 2':
        for key in 'x','y','q','pa','re','n':
            p[key] = dic[name+' '+key][a1,a2,a3]
    gals.append(SBModels.Sersic(name,p))

lenses = []
p = {}
for key in 'x','y','q','pa','b','eta':
    p[key] = dic['Lens 1 '+key][a1,a2,a3]
lenses.append(MassModels.PowerLaw('Lens 1',p))
p = {}
p['x'] = lenses[0].pars['x']
p['y'] = lenses[0].pars['y']
p['b'] = dic['extShear'][a1,a2,a3]
p['pa'] = dic['extShear PA'][a1,a2,a3]
lenses.append(MassModels.ExtShear('shear',p))

srcs = []
for name in ['Source 1']:
    p = {}
    if name == 'Source 1':
        print name
        for key in 'q','re','n','pa':
           p[key] = kdic[name+' '+key][ka1,ka2,ka3]
        for key in 'x','y': # subtract lens potition - to be added back on later in each likelihood iteration!
            p[key] = kdic[name+' '+key][ka1,ka2,ka3]+lenses[0].pars[key]
    srcs.append(SBBModels.Sersic(name,p))


dx = 0
dy = 0
#dx = kdic['xoffset'][ka1,ka2,ka3]
#dy = kdic['yoffset'][ka1,ka2,ka3]
xp,yp = xc+dx,yc+dy
imin,sigin,xin,yin = image[mask], sigma[mask],xp[mask2],yp[mask2]
n = 0
model = np.empty(((len(gals) + len(srcs)+1),imin.size))
for gal in gals:
    gal.setPars()
    tmp = xc*0.
    tmp[mask2] = gal.pixeval(xin,yin,1./OVRS,csub=23) # evaulate on the oversampled grid. OVRS = number of new pixels per old pixel.
    tmp = iT.resamp(tmp,OVRS,True) # convert it back to original size
    tmp = convolve.convolve(tmp,psf,False)[0]
    model[n] = tmp[mask].ravel()
    n +=1
for lens in lenses:
    lens.setPars()
x0,y0 = pylens.lens_images(lenses,srcs,[xin,yin],1./OVRS,getPix=True)
for src in srcs:
    src.setPars()
    tmp = xc*0.
    tmp[mask2] = src.pixeval(x0,y0,1./OVRS,csub=23)
    tmp = iT.resamp(tmp,OVRS,True)
    tmp = convolve.convolve(tmp,psf,False)[0]
    model[n] = tmp[mask].ravel()
    n +=1
model[n] = np.ones(model[n-1].size)
n+=1
rhs = (imin/sigin) # data
op = (model/sigin).T # model matrix
fit, chi = optimize.nnls(op,rhs)
components = (model.T*fit).T.reshape((n,image.shape[0],image.shape[1]))
model = components.sum(0)
SotPleparately(image,model,sigma,'V')
#for i in range(5):
#    pl.figure()
#    pl.imshow(components[i],interpolation='nearest',origin='lower')
#    pl.colorbar()
print fit

pl.figure()
pl.plot(klp[:,0])

## also print new source params
d = []
l,u = [], []
for key in kdic.keys():
    f = kdic[key][:,0].reshape((ktrace.shape[0]*ktrace.shape[2]))
    lo,med,up = np.percentile(f,50)-np.percentile(f,16), np.percentile(f,50), np.percentile(f,84)-np.percentile(f,50) 
    d.append((key,med))
    l.append((key,lo))
    u.append((key,up))

Ddic = dict(d)                    
Ldic = dict(l)
Udic = dict(u)

print r'\begin{table}[H]'
print r'\centering'
print r'\begin{tabular}{|c|cccccc|}\hline'
print r' object & x & y & re & n & pa & q \\\hline'
print 'source 1 & $', '%.2f'%(Ddic['Source 1 x']+lenses[0].pars['x']), '_{-', '%.2f'%Ldic['Source 1 x'],'}^{+','%.2f'%Udic['Source 1 x'], '}$ & $', '%.2f'%(Ddic['Source 1 y']+lenses[0].pars['y']),'_{-', '%.2f'%Ldic['Source 1 y'],'}^{+', '%.2f'%Udic['Source 1 y'], '}$ & $', '%.2f'%Ddic['Source 1 re'],'_{-', '%.2f'%Ldic['Source 1 re'],'}^{+', '%.2f'%Udic['Source 1 re'], '}$ & $', '%.2f'%Ddic['Source 1 n'],'_{-', '%.2f'%Ldic['Source 1 n'],'}^{+', '%.2f'%Udic['Source 1 n'], '}$ & $','%.2f'%Ddic['Source 1 pa'],'_{-', '%.2f'%Ldic['Source 1 pa'],'}^{+', '%.2f'%Udic['Source 1 pa'], '}$ & $','%.2f'%Ddic['Source 1 q'],'_{-', '%.2f'%Ldic['Source 1 q'],'}^{+', '%.2f'%Udic['Source 1 q'], '}$',r'\\'
print r'\end{tabular}'
print r'\end{table}'

np.save('/data/ljo31/Lens/radgrads/J1218_211_V',srcs)
