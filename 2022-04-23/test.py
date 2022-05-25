from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
data = pd.read_csv("E:/C.elegans_tracker/2022-02-16_Pflp22-gcamp-1.csv",header=None)
data = data.values
scale = 1.1
print(data)
x = []
y = []
for line in data:
    x.append(line[0] + (line[2] - 860) * scale)
    y.append(line[1] + (line[3] - 600) * scale)

plt.figure(figsize=(20,8),dpi=100)
plt.plot(x,y)
plt.show()