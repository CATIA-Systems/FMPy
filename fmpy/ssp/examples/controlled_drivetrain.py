"""
Example that demonstrates the simulation of SSPs (System Structure and Parameterization)
"""

from fmpy.ssp.simulation import simulate_ssp
from fmpy.util import download_file, plot_result


def simulate_controlled_drivetrain(show_plot=True):
    """ Download and simulate ControlledDrivetrain.ssp

    Parameters:
        show_plot     plot the results
    """

    ssp_filename = r'ControlledDrivetrain.ssp'

    download_file('https://github.com/CATIA-Systems/FMPy/releases/download/v0.1.1/' + ssp_filename, checksum='45e667ed')

    print("Simulating %s..." % ssp_filename)
    result = simulate_ssp(ssp_filename, stop_time=4, step_size=1e-3)

    if show_plot:
        print("Plotting results...")
        plot_result(result, names=['reference.y', 'drivetrain.w', 'controller.y'], window_title=ssp_filename)

    print('Done.')

    return result


if __name__ == '__main__':

    simulate_controlled_drivetrain()
