import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
import googleDriveFileLoader
#TODO: Data Analysis
# Resolve Peaks (Maxima)

filename = 'J532p5_T01_2hr270C_Sr12Pr88NiO3_STO.xrdml'
foldername = 'J532p5_Sr12Pr88NiO3_STO'
fLoader = googleDriveFileLoader.fileLoader(filename,foldername)

tth = fLoader.createDict()
