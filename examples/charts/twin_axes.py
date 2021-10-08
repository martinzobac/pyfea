import matplotlib.pyplot as plt
import random
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import ScalarFormatter

fig, ax1 = plt.subplots()
fig.subplots_adjust(right=0.75)

ax2 = ax1.twinx()
ax3 = ax1.twinx()

x = list()
y1 = list()
y2 = list()
y3 = list()

for i in range(25):
    x.append(i)
    y1.append(random.uniform(-10, 10))
    y2.append(random.uniform(-10, 10))
    y3.append(random.uniform(-10, 10))

    ax1.cla()
    p1, = ax1.plot(x, y1, 'bo-', label='bla')
    ax1.set_ylabel('bla')

    ax2.cla()
    p2, = ax2.plot(x, y2, 'r+-', label='ble')
    ax2.set_ylabel('ble')

    ax3.cla()
    p3, = ax3.plot(x, y3, 'g+-', label='blu')
    ax3.set_ylabel('blu')
    ax3.spines.right.set_position(("axes", 1.2))

    ax1.legend(handles=[p1, p2, p3])

    plt.show(block=False)
    plt.pause(0.01)

plt.show()



