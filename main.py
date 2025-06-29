import numpy as np
import matplotlib.pyplot as plt
import os
import glob

for p in glob.glob('output/*.png'):
    if os.path.isfile(p):
        os.remove(p)

x = np.arange(-5, 5, 0.1)
y = np.sin(x)

plt.plot(x, y)

plt.savefig("output/test2.png")
