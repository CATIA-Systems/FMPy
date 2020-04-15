import os
import shutil
import numpy as np

from fmpy import read_model_description, extract
from fmpy.fmi1 import FMU1Slave
from fmpy.fmi2 import FMU2Slave
from fmpy.ssp.ssd import System, read_ssd, get_connections, find_connectors, find_components


def get_value(component, name):
    """ Get a variable from a component """

    variable = component.variables[name]
    vr = [variable.valueReference]

    if variable.type == 'Real':
        return component.fmu.getReal(vr)[0]
    elif variable.type in ['Integer', 'Enumeration']:
        return component.fmu.getInteger(vr)[0]
    elif variable.type == 'Boolean':
        value = component.fmu.getBoolean(vr)[0]
        return value != 0
    else:
        raise Exception("Unsupported type: %s" % variable.type)


def set_value(component, name, value):
    """ Set a variable to a component """

    variable = component.variables[name]
    vr = [variable.valueReference]

    if variable.type == 'Real':
        component.fmu.setReal(vr, [float(value)])
    elif variable.type in ['Integer', 'Enumeration']:
        component.fmu.setInteger(vr, [int(value)])
    elif variable.type == 'Boolean':
        # TODO: convert literals
        component.fmu.setBoolean(vr, [value != 0.0])
    else:
        raise Exception("Unsupported type: %s" % variable.type)


def add_path(element, path=''):

    if isinstance(element, System):
        for child in element.elements:
            add_path(child, path + child.name + '.')

    for connector in element.connectors:
        connector.path = path + connector.name


def set_parameters(component, parameter_set):
    """ Apply the parameters (start values) to a component """

    path = component.name

    parent = component.parent

    while parent.parent is not None:
        path = parent.name + '.' + path
        parent = parent.parent

    for parameter in parameter_set.parameters:
        if parameter.name.startswith(path):
            variable_name = parameter.name[len(path) + 1:]
            set_value(component, variable_name, parameter.value)


def instantiate_fmu(component, ssp_unzipdir, start_time, stop_time=None, parameter_set=None):
    """ Instantiate an FMU """

    fmu_filename = os.path.join(ssp_unzipdir, component.source)

    component.unzipdir = extract(fmu_filename)

    # read the model description
    model_description = read_model_description(fmu_filename, validate=False)

    if model_description.coSimulation is None:
        raise Exception("%s does not support co-simulation." % component.source)

    # collect the value references
    component.variables = {}
    for variable in model_description.modelVariables:
        # component.vrs[variable.name] = variable.valueReference
        component.variables[variable.name] = variable

    fmu_kwargs = {'guid': model_description.guid,
                  'unzipDirectory': component.unzipdir,
                  'modelIdentifier': model_description.coSimulation.modelIdentifier,
                  'instanceName': component.name}

    if model_description.fmiVersion == '1.0':
        component.fmu = FMU1Slave(**fmu_kwargs)
        component.fmu.instantiate()
        if parameter_set is not None:
            set_parameters(component, parameter_set)
        component.fmu.initialize(stopTime=stop_time)
    else:
        component.fmu = FMU2Slave(**fmu_kwargs)
        component.fmu.instantiate()
        component.fmu.setupExperiment(startTime=start_time)
        if parameter_set is not None:
            set_parameters(component, parameter_set)
        component.fmu.enterInitializationMode()
        component.fmu.exitInitializationMode()


def free_fmu(component):
    """ Free an FMU and remove its unzip dir """

    component.fmu.terminate()
    component.fmu.freeInstance()
    try:
        shutil.rmtree(component.unzipdir)
    except Exception as e:
        print("Failed to remove unzip directory. " + str(e))


def do_step(component, time, step_size):
    """ Perform one simulation step """

    # set inputs
    for connector in component.connectors:
        if connector.kind == 'input':
            set_value(component, connector.name, connector.value)

    # do step
    component.fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)

    # get outputs
    for connector in component.connectors:
        if connector.kind == 'output':
            connector.value = get_value(component, connector.name)


def simulate_ssp(ssp_filename, start_time=0.0, stop_time=None, step_size=None, parameter_set=None, input={}):
    """ Simulate a system of FMUs """

    if stop_time is None:
        stop_time = 1.0

    if step_size is None:
        step_size = stop_time * 1e-2

    ssd = read_ssd(ssp_filename)

    add_path(ssd.system)

    components = find_components(ssd.system)
    connectors = find_connectors(ssd.system)
    connections = get_connections(ssd.system)

    # resolve connections
    connections_reversed = {}

    for a, b in connections:
        connections_reversed[b] = a

    new_connections = []

    # trace connections back to the actual start connector
    for a, b in connections:

        while isinstance(a.parent, System) and a.parent.parent is not None:
            a = connections_reversed[a]

        new_connections.append((a, b))

    connections = new_connections

    # extract the SSP
    ssp_unzipdir = extract(ssp_filename)

    # initialize the connectors
    for connector in connectors:
        connector.value = 0.0

    # instantiate the FMUs
    for component in components:
        instantiate_fmu(component, ssp_unzipdir, start_time, stop_time, parameter_set)

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

    for connector, value in zip(connectors, rows[0][1:]):
        if type(value) == bool:
            dtype.append((connector.path, np.bool_))
        elif type(value) == int:
            dtype.append((connector.path, np.int32))
        else:
            dtype.append((connector.path, np.float64))

    # convert the results to a structured NumPy array
    return np.array(rows, dtype=np.dtype(dtype))
