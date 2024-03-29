import numpy,os,pyfits as py
from scipy import sparse
from veldisp import veltools as T
from scipy.interpolate import splrep, splev
import pylab as pl

class dlambdaTemplates:

    def __init__(self,sigmaSci,nsigma=4.):
        self.sigmaSci = sigmaSci

        self.spex = []
        for obj in self.objs:
            w,s = numpy.loadtxt(obj).T
            self.spex.append(s)
        if w[0]<200.:
            w*=10.
        self.wave = w
        if self.res<50.:
            self.sigmaTemp = 299792.*self.res/w/2.355
        else:
            self.sigmaTemp = 299792./self.res/2.355 * numpy.ones(self.wave.size)
        self.sigma2diff = sigmaSci(w)**2-self.sigmaTemp**2
        self.nsigma = nsigma

    def getSpectra(self,wave,z,disp):
        wrest = wave/(1.+z)
        wcond = (self.wave>wrest.min()-75.)#self.nsigma*self.pixScale*30)
        wcond = wcond&(self.wave<wrest.max()+75.)#self.nsigma*self.pixScale*30)

        w = self.wave[wcond]
        X = numpy.arange(w.size)
        kernel = w*(disp**2+self.sigma2diff[wcond])**0.5/299792.

        kpix = kernel/self.pixScale
        bcond = ~numpy.isfinite(kpix)|(kpix<0.5)
        kpix[bcond] = 0
        kpix2 = kpix**2
        pmax = int(kpix.max()*self.nsigma+1)

        rcol = numpy.linspace(-pmax,pmax,2*pmax+1).repeat(X.size).reshape((2*pmax+1,X.size))
        col = rcol+X
        row = X.repeat(2*pmax+1).reshape((X.size,2*pmax+1)).T
        c = (col>=0)&(col<w.size)&(abs(rcol)<=self.nsigma*kpix[row])
        col = col[c]
        row = row[c]
        rcol = rcol[c]
        kpix2 = kpix2[row]
        wht = numpy.exp(-0.5*rcol*rcol/kpix2)/(self.norm*kpix[row])
        wht[bcond[row]] = 1.
        B = sparse.coo_matrix((wht,(row,col)),shape=(X.size,X.size))

        indx = (wrest-w[0])/(w[1]-w[0])
        lo = indx.astype(numpy.int32)
        hi = lo+1
        weights = 1.-numpy.concatenate((indx-lo,hi-indx))
        cols = numpy.concatenate((lo,hi))
        rows = numpy.concatenate((numpy.arange(lo.size),numpy.arange(lo.size)))
        cond = (cols<0)|(cols>=w.size)
        cols[cond] = 0
        weights[cond] = 0.
        
        I = sparse.coo_matrix((weights,(rows,cols)),shape=(lo.size,X.size))
        op = I*B

        ospex = []
        for spec in self.spex:
            #smooth = B*spec[wcond]
            #m = splrep(w,smooth,k=1)
            #new = splev(wrest,m)
            #interp = op*spec[wcond]
            #pl.figure()
            #pl.plot(w,smooth)
            #pl.plot(wrest,new)
            #pl.plot(wrest,interp)
            #pl.show()
            ospex.append(op*spec[wcond])

        return ospex

class dloglambdaTemplates:

    def __init__(self,sigmaSci,nsigma=4.):
        self.sigmaSci = sigmaSci

        self.spex = []
        for obj in self.objs:
            s = py.open(obj)[0].data.astype(numpy.float64)
            s /= s.mean()
            self.spex.append(s)
        self.wave = T.wavelength(self.objs[0],0)
        self.logwave = numpy.log10(self.wave)
        self.sigmaTemp = 299792.*self.res/self.wave/2.355
        self.sigma2diff = sigmaSci(self.wave)**2-self.sigmaTemp**2
        self.nsigma = nsigma
        self.pixScale = self.logpixscale*self.wave*numpy.log(10.)

    def getSpectra(self,logwave,z,disp):
        wrest = logwave - numpy.log10(1.+z)
        #wcond = (self.logwave>wrest.min()-self.nsigma*60*self.logpixscale*2)
        #wcond = wcond&(self.logwave<wrest.max()+self.nsigma*60*self.logpixscale*2)
        #print '1',numpy.where(self.logwave>numpy.log10(10**(wrest.min())-75.))
        #print '2',numpy.where(self.logwave<numpy.log10(10**(wrest.max())+75.)), (10**(wrest.max())+75.), 10**numpy.min(self.logwave)
        wcond = (self.logwave>numpy.log10(10**(wrest.min())-75.))
        wcond = wcond&(self.logwave<numpy.log10(10**(wrest.max())+75.))

        w = self.logwave[wcond]
        X = numpy.arange(w.size)
        kernel = (disp**2+self.sigma2diff[wcond])**0.5/299792.
        kpix = kernel/(self.logpixscale * numpy.log(10.))
        
        bcond = ~numpy.isfinite(kpix)|(kpix<0.5)
        kpix[bcond] = 0
        kpix2 = kpix**2
        pmax = int(kpix.max()*self.nsigma+1)

        rcol = numpy.linspace(-pmax,pmax,2*pmax+1).repeat(X.size).reshape((2*pmax+1,X.size))
        col = rcol+X
        row = X.repeat(2*pmax+1).reshape((X.size,2*pmax+1)).T
        c = (col>=0)&(col<w.size)&(abs(rcol)<=self.nsigma*kpix[row])
        col = col[c]
        row = row[c]
        rcol = rcol[c]
        kpix2 = kpix2[row]
        wht = numpy.exp(-0.5*rcol*rcol/kpix2)/(self.norm*kpix[row])
        wht[bcond[row]] = 1.
        B = sparse.coo_matrix((wht,(row,col)),shape=(X.size,X.size))

        indx = (wrest-w[0])/self.logpixscale
        
        lo = indx.astype(numpy.int32)
        hi = lo+1
        weights = 1.-numpy.concatenate((indx-lo,hi-indx))
        cols = numpy.concatenate((lo,hi))
        rows = numpy.concatenate((numpy.arange(lo.size),numpy.arange(lo.size)))

        cond = (cols<0)|(cols>=w.size)
        cols[cond] = 0
        weights[cond] = 0.

        I = sparse.coo_matrix((weights,(rows,cols)),shape=(lo.size,X.size))
        
        op = I*B
        ospex = []
        for spec in self.spex:
            #smooth = B*spec[wcond]
            #pl.plot(self.wave[wcond],smooth)
            #pl.plot(wave,op*spec[wcond])
            #pl.show()
            '''smooth = B*spec[wcond]
            m = splrep(w,smooth,k=1)
            new = splev(wrest,m)
            interp = op*spec[wcond]
            pl.figure()
            #pl.plot(w,smooth)
            pl.plot(wrest,new)
            pl.plot(wrest,interp)
            pl.show()'''
            ospex.append(op*spec[wcond])

        return ospex



class MILES(dlambdaTemplates):

    objs = ['0300','0268','0615','0667','0807','0729','0872','0602','0524']
#    objs += ['0632','0748'] # F/A stars
#    objs += ['0269','0080','0549','0245','0332','0286','0585','0198']  # Super-solar
#    objs += ['0287','0557','0189','0882','0195']

    dir = '/home/mauger/python/vdFit/miles/m'
    objs = [dir+obj+'V' for obj in objs]
    
    norm = (2*numpy.pi)**0.5

    nspex = len(objs)
    pixScale = 0.9
    res = 2.5

class BC03(dlambdaTemplates):

    dir='/data/ljo31b/EELs/esi/BC03/chab_'
    objs = ['2gyr','5gyr','6gyr','7gyr','7p5gyr','8gyr','9gyr']
    objs = [dir+obj+'.dat' for obj in objs]

    norm = (2*numpy.pi)**0.5

    nspex = len(objs)
    pixScale = 1.
    res = 3.

    
class INDOUS(dloglambdaTemplates):

    dir='/data/ljo31b/EELs/esi/INDOUS/'
    objs = ['102328_K3III.fits','163588_K2III.fits','107950_G5III.fits','124897_K1III.fits','168723_K0III.fits','111812_G0III.fits','148387_G8III.fits','188350_A0III.fits','115604_F2III.fits']
    objs = [dir+obj for obj in objs]

    norm = (2*numpy.pi)**0.5

    nspex = len(objs)
    logpixscale = 2.5e-5
    res = 1.2


class PICKLES(dlambdaTemplates):
    
    dir = '/data/ljo31b/EELs/esi/PICKLES/'
    objs = ['K3III.dat','K2III.dat','G5III.dat','K1III.dat','K0III.dat','G0III.dat','G8III.dat','A0III.dat','F2III.dat']
    objs = [dir+obj for obj in objs]

    norm = (2*numpy.pi)**0.5

    nspex = len(objs)
    pixScale = 5.
    res = 500.
