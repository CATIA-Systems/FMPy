from .simulation import simulate_fmu
from collections import Iterable
import sys
import matplotlib.pyplot as plt


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Usage:")
        print("> python -m fmpy.simulate <FMU>")
        exit(-1)

    filename = sys.argv[1]

    result = simulate_fmu(filename=filename)

    time = result['time']
    names = result.dtype.names[1:]

    if len(names) > 0:

        fig, axes = plt.subplots(len(names), sharex=True)

        fig.set_facecolor('white')

        if not isinstance(axes, Iterable):
            axes = [axes]

        for ax, name in zip(axes, names):
            ax.plot(time, result[name])
            ax.set_ylabel(name)
            ax.grid(True)
            ax.margins(y=0.1)

        plt.tight_layout()
        plt.show()
