import numpy as np, pylab as pl
from linslens import EELsKeckLensModels as K, EELsImages_huge as Image, EELsModels_huge as L
from linslens.Plotter import *
#from linslens.pixplot import *
import indexTricks as iT
from pylens import MassModels,pylens,adaptTools as aT,pixellatedTools as pT
from imageSim import SBModels,convolve
from scipy.sparse import diags
import pymc,cPickle
import myEmcee_blobs as myEmcee
from linslens.GrabImages_huge import *
import glob

''' lets do these one at a time for now, to avoid errors '''
''' start off with power laws '''
''' pixellated sources '''
''' band by band for now? pixellated sources on many bands? '''
def showRes(x,y,src,psf,img,sig,mask,iflt,vflt,cmat,reg,niter,npix,vmx,band):
    oy,ox = iT.coords((npix,npix))
    oy -= oy.mean()
    ox -= ox.mean()
    span = max(x.max()-x.min(),y.max()-y.min())
    oy *= span/npix
    ox *= span/npix
    ox += x.mean()
    oy += y.mean()
    lmat = psf*src.lmat
    rmat = src.rmat
    res,fit,model,rhs,regg = aT.getModelG(iflt,vflt,lmat,cmat,rmat,1,niter=niter)
    res,fit2,model,rhs,regg = aT.getModelG(iflt,vflt,lmat,cmat,rmat,1,niter=niter)

    osrc = src.eval(ox.ravel(),oy.ravel(),fit).reshape(ox.shape)

    oimg = img*np.nan
    oimg[mask] = (lmat*fit2)

    ext = [0,img.shape[1],0,img.shape[0]]
    ext2 = [x.mean()-span/2.,x.mean()+span/2.,y.mean()-span/2.,y.mean()+span/2.]

    pl.figure(figsize=(15,5))
    pl.subplot(131)
    pl.figtext(0.05,0.8,name,fontsize=30,color='white')
    pl.imshow(oimg,origin='lower',interpolation='nearest',extent=ext,vmin=0,vmax=1,cmap='jet',aspect='auto')
    pl.gca().xaxis.set_major_locator(pl.NullLocator())
    pl.gca().yaxis.set_major_locator(pl.NullLocator())
    #pl.colorbar()
    pl.subplot(132)
    resid = (img-oimg)/sig
    #resid[26:31,17:24] = np.random.randn(5,7)
    #resid[8:11,26:28] = np.random.randn(3,2)
    pl.imshow(resid,origin='lower',interpolation='nearest',extent=ext,vmin=-3,vmax=3,cmap='jet',aspect='auto')
    #pl.colorbar()
    pl.gca().xaxis.set_major_locator(pl.NullLocator())
    pl.gca().yaxis.set_major_locator(pl.NullLocator())
    pl.subplot(133)
    pl.imshow(osrc[100:-100,100:-100],origin='lower',interpolation='nearest',extent=ext,vmin=0,vmax=0.5,cmap='jet',aspect='auto')
    xstart = 5.
    xx = np.arange(xstart,xstart+21,1)
    yy = np.ones(xx.size)*5

    pl.plot(xx,yy,color='white',lw=4)
    pl.imshow(osrc[100:-100,100:-100],origin='lower',interpolation='nearest',extent=ext,vmin=0,vmax=1.75,cmap='jet',aspect='auto')
    pl.figtext(0.763,0.21,"$1''$",color='white',fontsize=45,weight=1000,family='sans-serif',stretch='ultra-expanded') 
    pl.gca().xaxis.set_major_locator(pl.NullLocator())
    pl.gca().yaxis.set_major_locator(pl.NullLocator())
    pl.savefig('/data/ljo31/Lens/TeXstuff/paper/phot_paper/'+name+'PIXALLFULL'+band+'.pdf')

    return osrc

   


def MakeModel(name,result,Npnts=1):
    
    lp,_,dic,_= result
    if len(lp.shape)==3.:
        lp = lp[:,0]
        for key in dic.keys():
            dic[key] = dic[key][:,0]
    a1,a2 = np.unravel_index(lp.argmax(),lp.shape)

    x_start, y_start = dic['Lens 1 x'][a1,a2],dic['Lens 1 y'][a1,a2]
    LX = x_start
    LY = y_start
    LB = dic['Lens 1 b'][a1,a2]
    LETA =dic['Lens 1 eta'][a1,a2]
    LQ = dic['Lens 1 q'][a1,a2]
    LPA = dic['Lens 1 pa'][a1,a2]
    SH = dic['extShear'][a1,a2]
    SHPA = dic['extShear PA'][a1,a2]

    lens = MassModels.PowerLaw('lens',{'x':LX,'y':LY,'b':LB,'eta':LETA,'q':LQ,'pa':LPA})
    shear = MassModels.ExtShear('shear',{'x':LX,'y':LY,'b':SH,'pa':SHPA})
    lenses = [lens,shear]

    # now set up the inference
    imgs = [img1,img2]
    sigs = [sig1,sig2]
    ifltms = [img[pix_mask] for img in imgs]
    sfltms = [sig[pix_mask] for sig in sigs]
    vfltms = [sfltm**2 for sfltm in sfltms]
    cmatms = [diags(1./sfltm,0) for sfltm in sfltms]
    xm,ym = x[pix_mask],y[pix_mask]
    coords = [[xm,ym],[xm+dic['xoffset'][a1,a2],ym+dic['yoffset'][a1,a2]]]

    # stellar mass deflection angles
    x_stars, y_stars = [V[0].flatten(), I[0].flatten()], [V[1].flatten(), I[1].flatten()]
    x_starms, y_starms = [V[0][pix_mask],I[0][pix_mask]], [V[1][pix_mask], I[1][pix_mask]]

    PSFs = [pT.getPSFMatrix(psf, img1.shape) for psf in [psf1,psf2]]
    PSFms = [pT.maskPSFMatrix(PSF,pix_mask) for PSF in PSFs]
    
    iflts = [img1.flatten(),img2.flatten()]
    sflts = [sig1.flatten(),sig2.flatten()]
    vflts = [sflt**2. for sflt in sflts]
    xflts = [x.flatten(), (x+dic['xoffset'][a1,a2]).flatten()]
    yflts = [y.flatten(), (y+dic['yoffset'][a1,a2]).flatten()]

    srcs = []
    for ii in range(len(iflts)-1):
        srcs.append(aT.AdaptiveSource(ifltms[ii]/sfltms[ii],ifltms[ii].size/Npnts))
        xl,yl = pylens.getDeflections(lenses,coords[ii])
        srcs[ii].update(xl,yl)

    import time
    reg=10.

    def doFit(p=None):
        global reg
        reg=10.
        lp = 0.
        #print '%.2f'%LB.value, '%.2f'%LX.value, '%.2f'%LY.value, '%.2f'%LETA.value, '%.2f'%LQ.value, '%.2f'%LPA.value
        for l in lenses:
            l.setPars()
        regs = []
        for ii in range(len(ifltms)-1): ### IMPORTANT - JUST DO THE V BAND FOR NOW!!!
            src,ifltm,sfltm,vfltm,PSFm,cmatm = srcs[ii],ifltms[ii],sfltms[ii],vfltms[ii],PSFms[ii],cmatms[ii]
            PSF,coord,iflt,sflt = PSFs[ii],coords[ii],iflts[ii],sflts[ii]
            x_star,y_star,x_starm,y_starm =x_stars[ii],y_stars[ii],x_starms[ii],y_starms[ii]
            xflt,yflt = xflts[ii],yflts[ii]

            xl,yl = pylens.getDeflections(lenses,coord)

            srcs[ii].update(xl,yl,doReg=True)
            lmat = PSFm*srcs[ii].lmat
            rmat = srcs[ii].rmat

            nupdate = 10
            res,fit,model,_,regg = aT.getModelG(ifltm,vfltm,lmat,cmatm,rmat,reg,nupdate)   
            reg = regg[0]
            regs.append(reg)
            xl,yl = pylens.getDeflections(lenses,[xflt,yflt])
            oimg,pix = srcs[ii].eval(xl,yl,fit,domask=False)
            oimg = PSF*oimg
            res = (iflt-oimg)/sflt
            lp+= -0.5*(res**2).sum()
        return regs
            
    # check initial model
    regs = doFit()
    #reg = 5.
    regs = doFit()
    print 'current regularisation (set by hand): ', '%.1f'%regs[0]
    vmxs = [1,3]
    bands = ['V','I']

    for ii in range(len(imgs)-1):
        src,ifltm,sfltm,vfltm,PSFm,cmatm = srcs[ii],ifltms[ii],sfltms[ii],vfltms[ii],PSFms[ii],cmatms[ii]
        x_star,y_star,x_starm,y_starm,PSF =x_stars[ii],y_stars[ii],x_starms[ii],y_starms[ii],PSFs[ii]
        img,sig,coord = imgs[ii],sigs[ii],coords[ii]
            
        xl,yl = pylens.getDeflections(lenses,coord)
        srcs[ii].update(xl,yl)
        osrc = showRes(xl,yl,srcs[ii],PSFm,img,sig,pix_mask,ifltm,vfltm,cmatm,regs[ii],0,400,vmx = vmxs[ii],band=bands[ii])
        pl.show()
    
    # now do some sampling. This will be slow -- make mask tighter?
  

# make image smaller
name = 'J1144'
file = py.open('/data/ljo31b/EELs/galsub/images/'+name+'_maxlnL.fits')
img1,img2 = file[1].data, file[2].data

# make images 120 pixels across
XX=24.
my,mx = img1.shape[0]/2., img1.shape[1]/2.
_,sig1,psf1,_,sig2,psf2,DX,DY,_,_ = EasyAddImages(name)
my -=3
img1,img2 = img1[my-XX:my+XX,mx-XX:mx+XX], img2[my-XX:my+XX,mx-XX:mx+XX]
sig1,sig2 = sig1[my-XX:my+XX,mx-XX:mx+XX],sig2[my-XX:my+XX,mx-XX:mx+XX]

psf1 = psf1/np.sum(psf1)
psf2 = psf2/np.sum(psf2)

y,x = iT.coords(img1.shape)
x,y = x+DX+(mx-XX), y+DY+(my-XX) 

pix_mask = py.open('/data/ljo31b/EELs/galsub/masks/'+name+'.fits')[0].data.copy()[my-XX:my+XX,mx-XX:mx+XX]
#pix_mask = py.open('/data/ljo31/Lens/J1125/maskneu.fits')[0].data.copy()[(my-50)-XX:(my-50)+XX,(mx-50)-XX:(mx-50)+XX]
pix_mask = np.ones(x.shape)
pix_mask = pix_mask==1

# stellar mass deflection angles
V,I,_ = np.load('/data/ljo31b/EELs/galsub/deflections/light_deflections_'+name+'.npy')
# make these the right shapes!
V = [V[ii][my-XX:my+XX,mx-XX:mx+XX] for ii in range(len(V))]
I = [I[ii][my-XX:my+XX,mx-XX:mx+XX] for ii in range(len(I))]

names = ['J0837','J0901','J0913','J1125','J1144','J1218','J1323','J1347','J1446','J1605','J1606','J1619','J2228']

dir = '/data/ljo31/Lens/LensModels/twoband/'
try:
    oresult = np.load(dir+name+'_212')
except:
    if name == 'J1347':
        oresult = np.load(dir+name+'_112')
    else:
        oresult = np.load(dir+name+'_211')

reg=10.
MakeModel(name,oresult)