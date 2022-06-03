"""This example shows the usage of a FMU in parameter optimizations.

The global minimum of the Eggholder function is searched for. It is implemented in two ways, in Python and in form of a
FMU (written in Modelica, compiled with Dymola 2023).

Different optimization algorithms from the scipy.optimize package are compared with respect to their convergence
velocities and a plot is created in which the different solution paths can be traced."""

from builtins import ValueError

import psutil
from scipy.optimize import differential_evolution, shgo, dual_annealing
from math import sin, sqrt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import fmpy
from fmpy import read_model_description, instantiate_fmu
from time import time
import os


workers = psutil.cpu_count(logical=False)
bounds = [(-512, 512),
          (-512, 512)]


def eggholder(x):
    # https://www.sfu.ca/~ssurjano/egg.html
    # Global minimum: eggholder([512, 404.2319]) = -959.6407
    y = -1*(x[1]+47)*sin(sqrt(abs(x[1]+x[0]/2+47)))-x[0]*sin(sqrt(abs(x[0]-(x[1]+47))))
    return y


def simulate_eggholder_fmu(x, unzipdir, model_description):
    """ Simulates eggholder FMU and returns y(x).
    """

    # Create a lasting instance to avoid repeated re-instantiation when calling this function repeatedly
    if not hasattr(simulate_eggholder_fmu, 'fmu_instance'):
        simulate_eggholder_fmu.fmu_instance = instantiate_fmu(unzipdir=unzipdir, model_description=model_description)
    else:
        simulate_eggholder_fmu.fmu_instance.reset()

    res = fmpy.simulate_fmu(filename=unzipdir,
                            start_time=0,
                            stop_time=1,
                            output_interval=1,
                            start_values=dict(zip(['x1', 'x2'], x)),
                            model_description=model_description,
                            fmu_instance=simulate_eggholder_fmu.fmu_instance,
                            output=['y'])

    return res['y'][-1]


def optimize_eggholder(method='differential_evolution', use_fmu=True):
    """ Optimizes the Eggholder function and returns the optimization results.

    Inputs:
        - method:   Select optimization algorithm. Selection options are: 'differential_evolution', 'shgo' and
                    'dual_annealing'.
        - use_fmu:  Select whether the FMU or the pure Python implementation should be used for the optimization.
    """

    if use_fmu:
        #unzipdir = fmpy.extract('../../tests/resources/eggholder.fmu')
        unzipdir = fmpy.extract(os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'resources', 'eggholder.fmu'))
        model_description = read_model_description(unzipdir)

    if method == 'differential_evolution':
        if use_fmu:
            res = differential_evolution(func=simulate_eggholder_fmu,
                                         bounds=bounds,
                                         args=(unzipdir, model_description),
                                         popsize=20,
                                         mutation=1.1,
                                         seed=1,
                                         polish=True,
                                         workers=workers,
                                         updating='deferred')
        else:
            res = differential_evolution(func=eggholder,
                                         bounds=bounds,
                                         popsize=20,
                                         mutation=1.1,
                                         seed=1,
                                         polish=True,
                                         workers=workers,
                                         updating='deferred')
    elif method == 'shgo':
        if use_fmu:
            res = shgo(func=simulate_eggholder_fmu,
                       bounds=bounds,
                       args=(unzipdir, model_description),
                       n=64,
                       sampling_method='sobol')
        else:
            res = shgo(func=eggholder,
                       bounds=bounds,
                       n=64,
                       sampling_method='sobol')
    elif method == 'dual_annealing':
        if use_fmu:
            res = dual_annealing(func=simulate_eggholder_fmu,
                                 bounds=bounds,
                                 args=(unzipdir, model_description),
                                 seed=4)
        else:
            res = dual_annealing(func=eggholder,
                                 bounds=bounds,
                                 seed=4)
    else:
        raise ValueError(f"Optimization method '{method}' not supported.")

    return res


_x_trace = list()


def _callback(x, convergence=None, f=None, context=None):
    _x_trace.append(x)


def plot_eggholder(trace_de=False, trace_shgo=False, trace_da=False):
    """ Create a plot of the eggholder function and, optionally, draws the optimization paths of the optimizers
    'differential_evolution', 'shgo' and 'dual_annelaing'.

    Input:
        - trace_de:     Select if trace of 'differential_evolution' algorithm is to be drawn
        - trace_shgo:   Select if trace of 'shgo' algorithm is to be drawn
        - trace_da:     Select if trace of 'dual_annealing' algorithm is to be drawn
    """
    x1 = np.linspace(bounds[0][0], bounds[0][1], 1000)
    x2 = np.linspace(bounds[1][0], bounds[1][1], 1000)

    X1, X2 = np.meshgrid(x1, x2)
    Y = np.empty(X1.shape)

    for i in range(X1.shape[0]):
        for j in range(X1.shape[1]):
            Y[i, j] = eggholder([X1[i, j], X2[i, j]])

    plt.contourf(X1, X2, Y, cmap=cm.YlGn)
    plt.title('Eggholder function')
    plt.xlabel("X1")
    plt.ylabel("X2")

    if trace_de:
        differential_evolution(func=eggholder,
                               bounds=bounds,
                               popsize=20,
                               mutation=1.1,
                               seed=1,
                               polish=False,
                               callback=_callback,
                               workers=workers,
                               updating='deferred')
        plt.plot([i[0] for i in _x_trace],
                 [i[1] for i in _x_trace],
                 marker='x',
                 color='dodgerblue',
                 label='differential_evolution')
        _x_trace.clear()

    if trace_shgo:
        shgo(func=eggholder,
             bounds=bounds,
             n=64,
             sampling_method='sobol',
             callback=_callback,
             minimizer_kwargs={'disp': False})
        plt.plot([i[0] for i in _x_trace],
                 [i[1] for i in _x_trace],
                 marker='x',
                 color='orange',
                 label='shgo')
        _x_trace.clear()

    if trace_da:
        dual_annealing(func=eggholder,
                       bounds=bounds,
                       seed=4,
                       callback=_callback)
        plt.plot([i[0] for i in _x_trace],
                 [i[1] for i in _x_trace],
                 marker='x',
                 color='orchid',
                 label='dual_annealing')
        _x_trace.clear()

    plt.plot(512, 404.2319, marker='o', color='r', label='global minimum')
    plt.legend()
    plt.colorbar()
    plt.show()


_start_time = 0


def tic():
    global _start_time
    _start_time = time()


def toc():
    elapsed_time = time() - _start_time
    print(f"Elapsed time is {elapsed_time:.6f} seconds.")


if __name__ == "__main__":
    print(f"Global minimum of eggholder function is {eggholder([512, 404.2319])} at [512, 404.2319].\n")

    for method in ['differential_evolution', 'shgo', 'dual_annealing']:
        tic()
        res = optimize_eggholder(method=method, use_fmu=True)
        print(f"Optimization method {method} returns {res.fun} at {res.x}.")
        toc()
        print('')

    plot_eggholder(trace_de=True, trace_shgo=True, trace_da=True)
