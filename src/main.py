import googleDriveFileLoader
import dataAnalyzer
import dataFormatter
import matplotlib.pyplot as plt

# Load Data 
#thin film file
# film_file = 'J465p6_T01_NdNiO3_STO_2hrs250C_15piecesCaH2.xrdml'
# film_folder = 'J465_NdNiO3_STO (p5 and p6)'
print()
print()
print("First, we will find the file you want to analyze.\nSecond, we will plot the data with no fit. You must close the plot to continue to the next step.\nThird, you will pick the range over which you want to fit the data. ")
film_file = input("Type in FILE Name of THIN FILM: ")
film_folder = input("Type in FOLDER Name of THIN FILM File: ")

#substrate file
# substrate_file = 'SrTiO3_001_substrate.xrdml'
# substrate_folder = 'SrTiO3_001_substrate'
substrate_file = input("Type in FILE Name of SUBSTRATE: ")
substrate_folder = input("Type in FOLDER Name of SUBSTRATE File: ")
#to make the outputs more readable
print()
print()

tth_thin_film = googleDriveFileLoader.fileLoader(film_file,film_folder)
tth_substrate = googleDriveFileLoader.fileLoader(substrate_file,substrate_folder)

Formatter = dataFormatter.Formatter()
Data = dataAnalyzer.Analyzer(tth_thin_film.createDict(),tth_substrate.createDict(),tth_thin_film.getKalpha2())
RAW_DATA = Data.FILM

# Analyze Data
Formatter.plotSemilogy(list(RAW_DATA.keys()),list(RAW_DATA.values()),20,60)
plt.show()

print()
print()
print("Enter the range of the data (in degrees) you want to be Gaussian fit")
X_MIN = float(input("Enter Minimum X: "))
X_MAX = float(input("Enter Maximum X: "))
tth0 = Data.initializeTheta(Data.FILM,1,10)
tth_fit = Data.regressionFit(tth0,5e-5,0.01,X_MIN,X_MAX)
dist = Data.braggsLaw(1,tth_fit[0],Data.KALPHA2)
#to make the outputs more readable
print()
print()

#Plot Data
d = Formatter.jupyterFormatter(Data.FILM,Data.FIT)
FIT_DATA = Data.FIT
Formatter.plotSemilogy(list(Data.FILM.keys()),list(Data.FILM.values()),X_MIN,X_MAX)
Formatter.plotSemilogy(list(FIT_DATA.keys()),list(FIT_DATA.values()),X_MIN,X_MAX)
plt.show()
print("This data will be uploaded to the Google Drive.")
ipynb_name = input("What would you like to name the Jupyter Notebook with this data? The .ipynb suffix will be automatically appended. ")
Formatter.createJupyterNB(ipynb_name,'Jupyter Notebooks', d)

# Create and upload Jupyter Notebook File
Formatter.createJupyterNB(ipynb_name,'Jupyter Notebooks', Formatter.jupyterFormatter(Data.FILM,Data.FIT))
tth_thin_film.uploadFile(ipynb_name,'Jupyter Notebooks/' + ipynb_name + '.ipynb','application/x-ipynb+json', tth_thin_film.FOLDER)

Formatter.plotSemilogy(list(Data.FILM.keys()),list(Data.FILM.values()),[float(i) for i in Data.FILM.keys()][0],[float(i) for i in Data.FILM.keys()][-1])
print()
print()

# Nelson Riley Fit
Data.nelsonRiley(90)
m, b = Data.nelsonRileyRegression()
Formatter.plotRiley(list(Data.SUBSTRATE.keys()),list(Data.SUBSTRATE.values()), [m*float(i) for i in Data.SUBSTRATE.keys()] + b )
print("Lattice constant calculated using Nelson-Riley method: " + str(b))
plt.show()



