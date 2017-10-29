import argparse
import textwrap

from .simulation import simulate_ssp
from .ssd import read_ssd
from ..util import plot_result

description = """\
Simulate an SSP

Example: 
    > python -m fmpy.ssp.simulate SampleSystem.ssp

"""

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description=textwrap.dedent(description))

parser.add_argument('ssp_filename', help="filename of the SSP")
parser.add_argument('--stop-time', type=float, help="stop time for the simulation")
parser.add_argument('--show-plot', action='store_true', help="plot the results")

args = parser.parse_args()

if __name__ == '__main__':

    result = simulate_ssp(args.ssp_filename, stop_time=args.stop_time)

    if args.show_plot:

        ssd = read_ssd(args.ssp_filename)
        names = []

        for connector in ssd.system.connectors:
            names.append(connector.name)

        plot_result(result=result, names=names, window_title=args.ssp_filename)
