import unittest
from fmpy import read_model_description, simulate_fmu
from fmpy.util import download_test_file
from fmpy.cswrapper import add_cswrapper


def add_cswrapper2(filename, outfilename=None):

    from fmpy.fmucontainer import Variable, Configuration, Component, create_fmu_container

    model_description = read_model_description(filename)

    model_identifier = model_description.modelExchange.modelIdentifier

    variables = []

    for variable in model_description.modelVariables:
        variables.append(Variable(
            type=variable.type,
            variability=variable.variability,
            causality=variable.causality,
            initial=variable.initial,
            name=variable.name,
            start=variable.start,
            description=variable.description,
            mapping=[(model_identifier, variable.name)]
        ))

    configuration = Configuration(
        variables=variables,
        components=[
            Component(
                filename=filename,
                interfaceType='ModelExchange',
                name=model_identifier
            )
        ]
    )

    create_fmu_container(configuration, outfilename)


class CSWrapperTest(unittest.TestCase):

    def test_cswrapper(self):

        filename = 'CoupledClutches.fmu'

        download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', filename)

        model_description = read_model_description(filename)

        self.assertIsNone(model_description.coSimulation)

        outfilename = filename[:-4] + '_cs.fmu'

        add_cswrapper(filename, outfilename=outfilename)

        simulate_fmu(outfilename, fmi_type='CoSimulation')

    def test_cswrapper2(self):

        filename = 'CoupledClutches.fmu'

        download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', filename)

        model_description = read_model_description(filename)

        self.assertIsNone(model_description.coSimulation)

        outfilename = filename[:-4] + '_cs2.fmu'

        add_cswrapper2(filename, outfilename=outfilename)

        simulate_fmu(outfilename, fmi_type='CoSimulation')
