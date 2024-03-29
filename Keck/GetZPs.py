import numpy as np, pylab as pl, pyfits as py
from linslens import EELsImages as E
from imageSim import SBObjects, convolve
import indexTricks as iT

# start with all narrow-camera objects!
ZPs = []
square,ap = 350,350

# K_2MASS(Vega)
K_2mass = dict([('J0837',15.074),('J0901',15.202),('J0913',0),('J1125',14.945),('J1144',15.107),('J1218',14.841),('J1248',14.670),('J1323',14.980),('J1347',15.341),('J1446',0),('J1605',15.216),('J1606',15.223),('J1619',14.853),('J2228',14.987)])
# uncertainties on the above (just in case!)
dK_2mass = dict([('J0837',0.115),('J0901',0.111),('J0913',0),('J1125',0.107),('J1144',0.110),('J1218',0.135),('J1248',0.098),('J1323',0.118),('J1347',0.195),('J1446',0.164),('J1605',0),('J1606',0.142),('J1619',0.094),('J2228',0.148)])
# entries are zero where system wasn't observed in 2MASS
Kcorr = 1.87

xk,yk = iT.coords((501,501))-250.
kern = SBObjects.Gauss('kernel',{'x':0,'y':0,'sigma':200./2.322,'q':1,'pa':0,'amp':1})
kernel = kern.pixeval(xk,yk)
kernel = kernel/np.sum(kernel)
def GetZP(image,kernel,square,ap,name,plot=False):
    kernelc = convolve.convolve(image,kernel)[1]
    blur = convolve.convolve(image,kernelc,False)[0]
    if plot:
       pl.figure()
       pl.imshow(blur,interpolation='nearest',origin='lower')
       pl.colorbar()
       pl.figure()
       pl.imshow(image,interpolation='nearest',origin='lower',vmin=0,vmax=4)#np.amax(image)*0.25)
       pl.colorbar()
       print np.sum(blur)/ np.sum(image) 
    y,x=iT.coords(image.shape)-square
    R=np.sqrt(x**2.+y**2.)
    flux = np.sum(blur[np.where(R<ap)])
    logged = -2.5*np.log10(flux)
    mag = K_2mass[name] + Kcorr
    print K_2mass[name]
    ZP = mag-logged
    return ZP#,blur

## J1323
s=200
image = py.open('/data/ljo31/Lens/J1323/J1323_nirc2.fits')[0].data.copy()[725-s+50:725+s,950-s:950+s]
mask = py.open('/data/ljo31/Lens/J1323/mask_Kp.fits')[0].data.copy()[725-s+50:725+s,950-s:950+s]
mask=mask==1
image[mask]=23
ZP = GetZP(image,kernel,s,s,'J1323',plot=False)
ZPs.append(('J1323',ZP))
print dict(ZPs)

# J0837
image = py.open('/data/ljo31/Lens/J0837/J0837_Kp_narrow_med.fits')[0].data.copy()[950-square:950+square,950-square:950+square]
ZP = GetZP(image,kernel,square,ap,'J0837',plot=False)
ZPs.append(('J0837',ZP))
print dict(ZPs)

# J0901
image = py.open('/data/ljo31/Lens/J0901/J0901_Kp_narrow.fits')[0].data.copy()[625-square:625+square,650-square:650+square]
ZP = GetZP(image,kernel,square,ap,'J0901',plot=False)
ZPs.append(('J0901',ZP))
print dict(ZPs)

# J0913 - doesn't have a measurement in 2MASS so add zero for now!!!
#s=300
#image = py.open('/data/ljo31/Lens/J0913/J0913_nirc2_n_Kp_6x6.fits')[0].data.copy()[300-s:300+s,300-s:300+s]
#ZP = GetZP(image,kernel,s,ap,'J0913',plot=True)
ZPs.append(('J0913',0))
print dict(ZPs)

# J1125
s=600
image = py.open('/data/ljo31/Lens/J1125/Kp_J1125_nirc2_n.fits')[0].data.copy()[775-s:775+s,775-s:775+s]
image[np.where(np.isnan(image)==True)] = 0.0
y,x=iT.coords(image.shape)
r=np.sqrt((x-s)**2. + (y-s)**2.)
image[(image<-2) & (r>200)] = 0.
image[(image>2) & (r>200)] = 0
ZP = GetZP(image,kernel,s,s,'J1125',plot=False)
ZPs.append(('J1125',ZP))
print dict(ZPs), 'J1125!!!'


# J1144
s=275
image = py.open('/data/ljo31/Lens/J1144/J1144_nirc2_n_Kp_6x6.fits')[0].data.copy()[275-s:275+s,300-s:300+s]
ZP = GetZP(image,kernel,s,s+100,'J1144',plot=False)
ZPs.append(('J1144',ZP))
print dict(ZPs)


# J1446 - nicht in 2MASS
#image = py.open('/data/ljo31/Lens/J0901/J0901_Kp_narrow.fits')[0].data.copy()[625-square:625+square,650-square:650+square]
#ZP = GetZP(image,kernel,square,ap,'J1323',plot=False)
ZPs.append(('J1446',0))
print dict(ZPs)

# J1605
s=250
image = py.open('/data/ljo31/Lens/J1605/J1605_Kp_narrow_med.fits')[0].data.copy()[650-s:650+s,700-s:700+s]
ZP = GetZP(image,kernel,s,s,'J1605',plot=False)
ZPs.append(('J1605',ZP))
print dict(ZPs)

## new pixel scale!
square,ap = 150,150
xk,yk = iT.coords((201,201))-100.
kern = SBObjects.Gauss('kernel',{'x':0,'y':0,'sigma':67./2.322,'q':1,'pa':0,'amp':1})
kernel = kern.pixeval(xk,yk)
kernel = kernel/np.sum(kernel)

# J1218
image = py.open('/data/ljo31/Lens/J1218/J1218_med.fits')[0].data.copy()[725-square:725+square,550-square:550+square]
ZP = GetZP(image,kernel,square,ap,'J1218',plot=False)
ZPs.append(('J1218',ZP))
print dict(ZPs)

# J1347
image = py.open('/data/ljo31/Lens/J1347/J1347_med.fits')[0].data.copy()[960-square:960+square,970-square:970+square]
ZP = GetZP(image,kernel,square,ap,'J1347',plot=False)
ZPs.append(('J1347',ZP))
print dict(ZPs)

# J1606
image = py.open('/data/ljo31/Lens/J1606/J1606_med.fits')[0].data.copy()[725-square:725+square,950-square:950+square]
ZP = GetZP(image,kernel,square,ap,'J1606',plot=False)
ZPs.append(('J1606',ZP))
print dict(ZPs)

# J2228
image = py.open('/data/ljo31/Lens/J2228/J2228_med.fits')[0].data.copy()[640-square:640+square,640-square:640+square]
ZP = GetZP(image,kernel,square,ap,'J2228',plot=False)
ZPs.append(('J2228',ZP))
print dict(ZPs)


np.save('/data/ljo31/Lens/LensParams/Keck_zeropoints',dict(ZPs))

