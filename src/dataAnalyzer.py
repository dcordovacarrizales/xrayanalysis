import numpy as np
import math
from scipy.signal import argrelextrema
from scipy.signal import find_peaks

class Analyzer:

    def __init__(self,data_film,data_substrate,kAlpha2):
        self.FILM = data_film
        self.SUBSTRATE = data_substrate
        self.KALPHA2 = kAlpha2
        self.FIT = None

    #Return a numpy array gaussian distribution.
    def gaussianFunc(self,x,x0,sigma):
        return np.exp(-(x-x0) ** 2 / (2 * sigma ** 2))

    # Return a numpy array lorentzian distribution.
    def lorentzianFunc(self,x,x0,tau):
        return (1 / np.pi) * (1/2 * tau) / ((x-x0) ** 2 + (1/2*tau) ** 2)

    # Return the fwhm and incr for the Smooth function.
    def getwidth_incr(self,x,sigma,std):
        fwhm = sigma * np.sqrt(8 * np.log(2))
        incr = x[1] - x[0]
        ind_incr = int(round(std*fwhm/incr))
        return (ind_incr,fwhm)

    # Returns a pseudo_voigt function (gaussian and lorenztian) based off of params
    def pseudoVoigt(self,data,sigma,std,eta):
        x = np.array(list(data.keys()))
        y = np.array(list(data.values()))
        pseudo_voigt = np.zeros(y.shape)
        incr,fwhm = self.getwidth_incr(x,sigma,std)
        x = np.pad(x,incr)
        y = np.pad(y,incr)

        for i in range(len(x)-2*incr):
            gaussian = self.gaussianFunc(x[i:i+2*incr],x[i+incr],sigma)
            gaussian = gaussian/ sum(gaussian) # normalize gaussian
            lorentzian = self.lorentzianFunc(x[i:i+2*incr],x[i+incr],fwhm)
            lorentzian = lorentzian/ sum(lorentzian) # normalize lorentzian
            pseudo_voigt[i] = sum(eta * y[i:i+2*incr] * gaussian + (1-eta) * y[i:i+2*incr] * lorentzian)
        return pseudo_voigt

    def initializeTheta(self,data,nth_peak,prominence):
        x = np.array(list(data.keys()))
        y = np.array(list(data.values()))
        peaks, _ = find_peaks(self.pseudoVoigt(data,0.05,2.7,1), prominence = prominence)
        x0 = x[peaks[nth_peak]]
        yp = y[peaks[nth_peak]]
        sigma = np.random.rand()
        b = 0
        return [x0,yp,sigma,b]

    # Align substrate to film
    # Take the peak values of the thin film peak, and shift the SUBSTRATE.values() over by set amt.
    def alignSubstrate(self):
        # peak values of self.FILM, self.SUBSTRATE
        filmValues = [float(i) for i in self.FILM.values()]
        substrateValues = [float(i) for i in self.SUBSTRATE.values()]

        filmKeys = [float(i) for i in self.FILM.keys()]
        substrateKeys = [float(i) for i in self.SUBSTRATE.keys()]

        filmPeaks, _ = find_peaks(filmValues, prominence = 90)
        substratePeaks, _ = find_peaks(substrateValues, prominence = 90)
        
        # the y values of the peaks
        filmPeakY = [float(filmValues[i]) for i in filmPeaks]
        substratePeakY = [float(substrateValues[i]) for i in substratePeaks]
        # the x values of the peaks
        filmPeakX = [float(filmKeys[i]) for i in filmPeaks]
        substratePeakX = [float(substrateKeys[i]) for i in substratePeaks]

        factors = []
        closeNum = []
        for i in range(len(substratePeaks)):
            x = np.array(filmPeakX)
            a = np.array(substratePeakX[i])
            closeNum.append(x[(np.abs(x-a)).argmin()])
            factors.append(substratePeakY[i] / filmPeakY[filmPeakX.index(closeNum[i])])
        # Scale self.SUBSTRATE to match self.FILM
        scaledFilmData = {}
        scaledFilmYValues = [float(i)*factors[0] for i in filmValues]
        xShift = closeNum[0] - substratePeakX[0]
        for i in range(len(filmKeys)):
            key = float(filmKeys[i]) + xShift
            scaledFilmData[key] = scaledFilmYValues[i]
        self.FILM = scaledFilmData

    # Curve fits data to a gaussian function within the min_x and max_x params
    def regressionFit(self,theta0,eta,epsilon,min_x,max_x):
        x = np.array(list(self.FILM.keys()))
        
        #smooth substrate data
        smoothed_substrate = self.pseudoVoigt(self.SUBSTRATE,0.05,2.7,1)
        
        #resize smoothed_film to match substrate
        smoothed_film = np.array(self.pseudoVoigt(self.FILM,0.05,2.7,1))
        smoothed_film.resize(smoothed_substrate.size)
        smoothed_film = np.array(smoothed_film)

        y = smoothed_film - smoothed_substrate # subtract smoothed film data from smoothed substrate data
        [x0,yp,sigma,b] = theta0
        prev_J = 0.0
        counts = 0
        N = int(len((np.where(x>min_x) and np.where(x<max_x)[0])))
        while True:
            prev_error = J = 0.0

            # Adjust x0
            while True:
                deltaJ_x0 = 0
                for i in np.where((x>min_x) & (x<max_x))[0]:
                    h = (yp / (sigma * np.sqrt(2*np.pi))) * self.gaussianFunc(x[i],x0,sigma) + b
                    COEFF = (yp * (x[i] - x0)/(sigma ** 2 * np.sqrt(2*np.pi))) 
                    EXP = np.exp(-(x[i]-x0) ** 2 / (2 * sigma ** 2))
                    deltaJ_x0 = deltaJ_x0 + (2/N) * (h - y[i]) * 2 * COEFF * EXP
                    J = J + (2/N) * (h - y[i]) ** 2   # (1e-4) scalar prevents J from overflowing
                x0 = x0 - eta * deltaJ_x0
                error = deltaJ_x0 ** 2
                if (abs(error - prev_error) < epsilon):
                    break
                prev_error = error

            # Adjust yp 
            prev_error = 0.0
            while True:   
                deltaJ_yp = 0.0
                COEFF = 1 / (sigma * np.sqrt(2*np.pi))
                for i in np.where((x>min_x) & (x<max_x))[0]:
                    h = (yp / (sigma * np.sqrt(2*np.pi))) * self.gaussianFunc(x[i],x0,sigma) + b
                    EXP = np.exp(-(x[i]-x0) ** 2 / (2 * sigma ** 2))
                    deltaJ_yp = deltaJ_yp + (2/N) * (h - y[i])* COEFF * EXP
                    J = J + (2/N) * (h - y[i])**2
                yp = yp - (1e4) * eta * deltaJ_yp
                error = deltaJ_yp ** 2
                if (abs(error - prev_error) < epsilon):
                    break
                prev_error = error

            # Adjust sigma
            prev_error = 0.0
            while True:
                deltaJ_sigma = 0
                for i in np.where((x>min_x) & (x<max_x))[0]:
                    h = (yp / (sigma * np.sqrt(2*np.pi))) * self.gaussianFunc(x[i],x0,sigma) + b
                    COEFF = (yp / (2 * np.pi)) * (((x[i]-x0) ** 2 / sigma ** 4) - (1 / sigma ** 2))
                    EXP = np.exp(-(x[i]-x0) ** 2 / (2 * sigma ** 2))
                    deltaJ_sigma = deltaJ_sigma + (2/N) * (h - y[i]) * COEFF * EXP
                    J = J + (2/N) * (h - y[i]) ** 2
                sigma = sigma - eta * deltaJ_sigma
                error = deltaJ_sigma ** 2
                if (abs(error - prev_error) < epsilon):
                    break
                prev_error = error

            # Adjust b
            prev_error = 0.0
            while True:
                deltaJ_b = 0
                for i in np.where((x>min_x) & (x<max_x))[0]:
                    h = (yp / (sigma * np.sqrt(2*np.pi))) * self.gaussianFunc(x[i],x0,sigma) + b
                    deltaJ_b = deltaJ_b  + (2/N) * (h - y[i]) 
                    J = J + (2/N) * (h - y[i]) ** 2
                b = b - (1e4) * eta * deltaJ_b
                error = deltaJ_b ** 2
                if (abs(error - prev_error) < epsilon):
                    break
                prev_error = error

            if (abs(J - prev_J) < epsilon) or counts > 1000:
                break
            prev_J = J
            counts = counts + 1

        self.FIT = dict(zip(x, (yp/ (sigma * np.sqrt(2*np.pi))) * self.gaussianFunc(x,x0,sigma) + b + self.pseudoVoigt(self.SUBSTRATE,0.05,2.7,1)))  
        return [x0,yp,sigma,b]
    
        

    def braggsLaw(self,n,theta,lbda):
        d = (n * lbda) / (2 * math.sin(math.radians(theta / 2)))
        return '{:.3f}'.format(d)
    
    # Nelson-Riley
    def nelsonRiley(self, prom):
        substrateValues = [float(i) for i in self.SUBSTRATE.values()]
        substrateKeys = [float(i) for i in self.SUBSTRATE.keys()]

        substratePeaks, _ = find_peaks(substrateValues, prominence = prom)
        substratePeakX = [float(substrateKeys[i]) for i in substratePeaks]

        newSubstrateKeys = []
        newSubstrateValues = []
        for i in range(len(substratePeakX)):
            theta = substratePeakX[i]
            newSubstrateValues.append(float(self.braggsLaw(i+1, theta, self.KALPHA2)))
            newSubstrateKeys.append(0.5*( ((math.cos(theta)**2)/(math.sin(theta))) + ((math.cos(theta)**2)/theta) ))
        nrfit = {}
        for i in range(len(newSubstrateKeys)):
            nrfit[newSubstrateKeys[i]] = newSubstrateValues[i]
        self.SUBSTRATE = nrfit
        
    # Nelson-Riley Regression Line 
    def nelsonRileyRegression(self):
        substrateValues = [float(i) for i in self.SUBSTRATE.values()]
        substrateKeys = [float(i) for i in self.SUBSTRATE.keys()]

        m, b = np.polyfit(np.array(substrateKeys), np.array(substrateValues), 1)
        return m, b
        




    