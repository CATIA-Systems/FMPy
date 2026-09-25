from fmpy.ssp.ssd import Component, Connection, Connector, System, build_path, get_connections


def _system_with_output_connector_as_source():
    """A root system whose output connector is the SOURCE of a connection.

    SSP writes "this endpoint is the enclosing system's own connector" by
    omitting startElement/endElement. Both directions are legal, and a system
    output connector that also feeds a component is what an SSP authoring tool
    produces when a signal must be both recorded at the top level and routed
    back into the system.
    """
    system = System(name='root')
    system.parent = None

    system_connector = Connector(name='M_load', kind='output')
    system_connector.parent = system
    system.connectors = [system_connector]

    component = Component(name='stimuli', source='stimuli.fmu')
    component.parent = system
    component_connector = Connector(name='M_load', kind='input')
    component_connector.parent = component
    component.connectors = [component_connector]
    system.elements = [component]

    system.connections = [
        Connection(startElement=None, startConnector='M_load',
                   endElement='stimuli', endConnector='M_load')
    ]

    return system, system_connector, component_connector


def test_get_connections_with_system_connector_as_source():
    """The system connector is the start of the connection, the component the end."""

    system, system_connector, component_connector = \
        _system_with_output_connector_as_source()

    connections = get_connections(system)

    assert (system_connector, component_connector) in connections, \
        "the system's output connector must be wired to the component's input"


def test_get_connections_with_system_connector_as_target():
    """The mirror image, which has always worked -- kept so the two stay in step."""

    system = System(name='root')
    system.parent = None

    system_connector = Connector(name='y', kind='output')
    system_connector.parent = system
    system.connectors = [system_connector]

    component = Component(name='plant', source='plant.fmu')
    component.parent = system
    component_connector = Connector(name='y', kind='output')
    component_connector.parent = component
    component.connectors = [component_connector]
    system.elements = [component]

    system.connections = [
        Connection(startElement='plant', startConnector='y',
                   endElement=None, endConnector='y')
    ]

    connections = get_connections(system)

    assert (component_connector, system_connector) in connections


def test_build_path():

    system = System(name='root')
    system.parent = None
    component = Component(name='plant', source='plant.fmu')
    component.parent = system
    connector = Connector(name='y', kind='output')
    connector.parent = component

    assert build_path(connector) == 'root.plant.y'
