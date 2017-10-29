import os
import shutil
import numpy as np

from fmpy import read_model_description, extract
from fmpy.fmi1 import FMU1Slave
from fmpy.fmi2 import FMU2Slave
from fmpy.ssp.ssd import System, read_ssd, get_connections, find_connectors, find_components, build_path


def get_real(component, name):
    """ Get a Real variable from a component """

    vr = component.vrs[name]
    return component.fmu.getReal([vr])[0]


def set_real(component, name, value):
    """ Set a Real variable to a component """

    vr = component.vrs[name]
    component.fmu.setReal([vr], [value])


def add_path(element, path=''):

    if isinstance(element, System):
        for child in element.elements:
            add_path(child, path + child.name + '.')

    for connector in element.connectors:
        connector.path = path + connector.name


def set_parameters(component, parameters):
    """ Apply the parameters (start values) to a component """

    path = component.name

    parent = component.parent

    while parent.parent is not None:
        path = parent.name + '.' + path
        parent = parent.parent

    for name, value in parameters.items():
        if name.startswith(path):
            variable_name = name[len(path) + 1:]
            set_real(component, variable_name, value)


def instantiate_fmu(component, ssp_unzipdir, start_time, parameters={}):

    fmu_filename = os.path.join(ssp_unzipdir, component.source)

    component.unzipdir = extract(fmu_filename)

    # read the model description
    model_description = read_model_description(fmu_filename, validate=False)

    # collect the value references
    component.vrs = {}
    for variable in model_description.modelVariables:
        component.vrs[variable.name] = variable.valueReference

    fmu_kwargs = {'guid': model_description.guid,
                  'unzipDirectory': component.unzipdir,
                  'modelIdentifier': model_description.coSimulation.modelIdentifier,
                  'instanceName': component.name}

    if model_description.fmiVersion == '1.0':
        component.fmu = FMU1Slave(**fmu_kwargs)
        component.fmu.instantiate()
        set_parameters(component, parameters)
        component.fmu.initialize()
    else:
        component.fmu = FMU2Slave(**fmu_kwargs)
        component.fmu.instantiate()
        component.fmu.setupExperiment(startTime=start_time)
        set_parameters(component, parameters)
        component.fmu.enterInitializationMode()
        component.fmu.exitInitializationMode()


def free_fmu(component):

    component.fmu.terminate()
    component.fmu.freeInstance()
    shutil.rmtree(component.unzipdir)


def do_step(component, time, step_size):

    # set inputs
    for connector in component.connectors:
        if connector.kind == 'input':
            set_real(component, connector.name, connector.value)

    # do step
    component.fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)

    # get outputs
    for connector in component.connectors:
        if connector.kind == 'output':
            connector.value = get_real(component, connector.name)


def simulate_ssp(ssp_filename, start_time=0.0, stop_time=None, step_size=None, parameters={}, input={}):
    """ Simulate a system of FMUs """

    if stop_time is None:
        stop_time = 1.0

    if step_size is None:
        step_size = stop_time * 1e-2

    ssd = read_ssd(ssp_filename)

    ssp_unzipdir = extract(ssp_filename)

    add_path(ssd.system)

    components = find_components(ssd.system)
    connectors = find_connectors(ssd.system)
    connections = get_connections(ssd.system)

    # initialize the connectors
    for connector in connectors:
        connector.value = 0.0

    # instantiate the FMUs
    for component in components:
        instantiate_fmu(component, ssp_unzipdir, start_time, parameters)

    time = start_time

    rows = []  # list to record the results

    # simulation loop
    while time < stop_time:

        # apply input
        for connector in ssd.system.connectors:
            if connector.kind == 'input' and connector.name in input:
                connector.value = input[connector.name](time)

        # perform one step
        for component in components:
            do_step(component, time, step_size)

        # apply connections
        for start_connector, end_connector in connections:
            end_connector.value = start_connector.value

        # get the results
        row = [time]

        for connector in connectors:
            row.append(connector.value)

        # append the results
        rows.append(tuple(row))

        # advance the time
        time += step_size

    # free the FMUs
    for component in components:
        free_fmu(component)

    # clean up
    shutil.rmtree(ssp_unzipdir)

    dtype = [('time', np.float64)]

    for connector in connectors:
        dtype.append((connector.path, np.float64))

    # convert the results to a structured NumPy array
    return np.array(rows, dtype=np.dtype(dtype))
