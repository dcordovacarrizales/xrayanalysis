import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import ntpath

from scipy.signal import find_peaks
import googleDriveFileLoader
#TODO: Data Analysis
# Resolve Peaks (Maxima)

filename1 = 'J465p5_T01_NdNiO3_STO_2hrs250C_2piecesCaH2.xrdml'
foldername1 = 'J465 CaH2 test'
filename2 = 'J465p6_T01_NdNiO3_STO_2hrs250C_15piecesCaH2.xrdml'
foldername2 = 'J465 CaH2 test'

fLoader1 = googleDriveFileLoader.fileLoader(filename1,foldername1)
fLoader2 = googleDriveFileLoader.fileLoader(filename2,foldername2)
tth1 = fLoader1.createDict()

#Return peak centers and amplitudes 
def getPeaks(x, y, peaks):
  xVal = x[peaks]
  yVal = y[peaks]
  peakTuple = []
  print(len(peaks))
  for i in range (len(peaks)):
    peakTuple.append((xVal[i], yVal[i]))
  return print(peakTuple)

def gaussianFunc(x,x0,sigma):
  #Return a numpy array gaussian distribution.
  return np.exp(-(x-x0) ** 2 / (2 * sigma ** 2))

def lorentzianFunc(x,x0,tau):
  # Return a numpy array lorentzian distribution.
  return (1 / np.pi) * (1/2 * tau) / ((x-x0) ** 2 + (1/2*tau) ** 2)

def getwidth_incr(x,sigma,std):
  # Return the fwhm and incr for the Smooth function.
  fwhm = sigma * np.sqrt(8 * np.log(2))
  incr = x[1] - x[0]
  ind_incr = int(round(std*fwhm/incr))
  return (ind_incr,fwhm)

def Smooth(x,y,sigma,std,weightG,weightL):
  #Returns the gaussian/lorenztian smoothed data.
  smoothed_vals = np.zeros(y.shape)
  incr,fwhm = getwidth_incr(x,sigma,std)
  x = np.pad(x,incr)
  y = np.pad(y,incr)

  for i in range(len(x)-2*incr):
    gaussian = gaussianFunc(x[i:i+2*incr],x[i+incr],sigma)
    gaussian = gaussian/ sum(gaussian)
    lorentzian = lorentzianFunc(x[i:i+2*incr],x[i+incr],fwhm)
    smoothed_vals[i] = sum(weightG * y[i:i+2*incr] * gaussian + weightL * y[i:i+2*incr] * lorentzian)
  return smoothed_vals

# Returns the file name from a path 
def fileName(file):
    head, tail = ntpath.split(file)
    return tail or ntpath.basename(head)

# Outputs rangeslider style graph including: raw data, smoothed data, and peaks based off of smoothed data for a single dataset 
def rangeSlider(x,y):
  # Loads the data 
  data = {'x': x, 'y':y}
  df = pd.DataFrame(data)

  # Smooth Data
  peaksApprox, _ = find_peaks(Smooth(x,y,0.1, 2, 0.5, 0.5), prominence = 80 )
  xValApprox = x[peaksApprox]
  yValApprox = Smooth(x,y,0.1, 2, 0.5, 0.5)[peaksApprox]

  # Creates the figure
  fig = go.Figure()
  # Adds raw data 
  fig.add_trace(
    go.Scatter(x=list(df.x), y=list(df.y), name = "data")
  )
  
  # Adds the smoothing 
  fig.add_trace(
    go.Scatter(x = x, y =Smooth(x,y,0.1, 2, 0.5, 0.5), name = "approximation" )
  )
  
  #Adds the peaks from the smooth graph
  fig.add_trace(
    go.Scatter(x = xValApprox, y =yValApprox, mode='markers', name = "peaks")
  )

  # Set the title
  fig.update_layout(
    title_text=fileName(infile)
  )
  
  # Add range slider
  fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(label = "all", step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        )
    ),
    yaxis_type="log",
    xaxis_title="2 Theta",
    yaxis_title="Intensity",
  )
  fig.show()
  
# Stacks graphs on top of each other 
def stackGraphs(x1, y1, x2, y2, peakProm):
  # Create figure
  fig = go.Figure()
 
  # Smooth Data
  peaksApprox1, _ = find_peaks(Smooth(x1,y1,0.1, 2, 0.5, 0.5), prominence = int(peakProm))
  xValApprox1 = x1[peaksApprox1]
  yValApprox1 = Smooth(x1,y1,0.1, 2, 0.5, 0.5)[peaksApprox1]

  peaksApprox2, _ = find_peaks(Smooth(x2,y2,0.1, 2, 0.5, 0.5), prominence = int(peakProm))
  xValApprox2 = x2[peaksApprox2]
  yValApprox2 = Smooth(x2,y2,0.1, 2, 0.5, 0.5)[peaksApprox2]

  # Raw Data
  coordinates1, coordinates2 = [], []
  for i in range(len(x1)):
    coordinates1.append((x1[i], y1[i]))
  for i in range(len(x2)):
    coordinates2.append((x2[i], y2[i]))

  coordinates1 = [str(num) for num in coordinates1]
  coordinates2 = [str(num) for num in coordinates2]

  # First Data Trace
  fig.add_trace(go.Scatter(
    x=[str(num) for num in x1],
    y=[str(num) for num in y1],
    name=filename1,
    text=coordinates1,
    yaxis="y"
  ))
  
  # First Smooth Data 
  fig.add_trace(go.Scatter(
    x=x1,
    y=Smooth(x1,y1,0.1, 2, 0.5, 0.5),
    name=filename1,
    yaxis="y"
  ))

  # First Smooth Peaks 
  fig.add_trace(go.Scatter(
    x=xValApprox1,
    y=yValApprox1,
    name=filename1,
    yaxis="y",
    mode='markers',
    text = xValApprox1
  ))

  #Second Data Trace 
  fig.add_trace(go.Scatter(
    x=[str(num) for num in x2],
    y=[str(num) for num in y2],
    name=filename2,
    text=coordinates2,
    yaxis="y2",
  ))

  # Second Smooth Data 
  fig.add_trace(go.Scatter(
    x=x_vals2,
    y=Smooth(x2,y2,0.1, 2, 0.5, 0.5),
    name=filename2,
    yaxis="y2"
  ))

  # Second Smooth Peaks 
  fig.add_trace(go.Scatter(
    x=xValApprox2,
    y=yValApprox2,
    name=filename2,
    yaxis="y2",
    mode='markers',
    text = xValApprox2
  ))

  # style all the traces
  fig.update_traces(
      hoverinfo="text+name",
      line={"width": 0.5},
      marker={"size": 8},
      showlegend=False
  )

  # Update axes
  fig.update_layout(
      xaxis=dict(
          autorange=True,
          range=[min([float(num) for num in x1]), max([float(num) for num in x1])],
          rangeslider=dict(
              autorange=True,
              range=[min(x1), max(x1)]
          ),
          type="linear",
          title = '2Theta'
      ),
      yaxis=dict(
          anchor="x",
          autorange=True,
          domain=[0, 0.5],
          linecolor="#673ab7",
          mirror=True,
          range=[min([float(num) for num in y1]), max([float(num) for num in y1])],
          showline=True,
          side="right",
          tickfont={"color": "#673ab7"},
          tickmode="auto",
          ticks="",
          titlefont={"color": "#673ab7"},
          type="log",
          zeroline=False,
          title = 'Intensity'
      ),
      yaxis2=dict(
          anchor="x",
          autorange=True,
          domain=[0.5, 1],
          linecolor="#E91E63",
          mirror=True,
          range=[min([float(num) for num in y2]), max([float(num) for num in y2])],
          showline=True,
          side="right",
          tickfont={"color": "#E91E63"},
          tickmode="auto",
          ticks="",
          titlefont={"color": "#E91E63"},
          type="log",
          zeroline=False,
          title = 'Intensity'
      )
  )

  # Updates the layout 
  fig.update_layout(
      dragmode="zoom",
      legend=dict(traceorder="reversed"),
      height=600,
      template="plotly_white",
      margin=dict(
          t=100,
          b=100
      ),
  )

  fig.show()

x_vals,y_vals = np.array(list(tth.keys())),np.array(list(tth.values()))

x_vals2, y_vals2 = np.array(list(tth2.keys())),np.array(list(tth2.values()))

peakProminence = input("Enter Prominence for Peaks: ")
stackGraphs(x_vals,y_vals, x_vals2, y_vals2, peakProminence)