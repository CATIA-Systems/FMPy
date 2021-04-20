""" Validation of the modelDescription.xml """


def validate_fmu(filename):
    """ Validate the following aspects of an FMU

    modelDescription.xml:
    - validation against the XML schema
    - uniqueness and validity of variable names
    - completeness and integrity of the ModelStructure
    - required start values
    - combinations of causality and variability
    - units

    Parameters:
        filename  filename of the FMU, directory with extracted FMU or file like object

    Returns:
        a list of the problems found
    """

    from . import read_model_description
    from .model_description import ValidationError

    problems = []

    try:
        read_model_description(filename,
                               validate=True,
                               validate_variable_names=True,
                               validate_model_structure=True)
    except ValidationError as e:
        problems = e.problems
    except Exception as e:
        problems = [str(e)]

    return problems


def validate_model_description(model_description, validate_variable_names=False, validate_model_structure=False):
    problems = []

    if validate_variable_names:
        problems += _validate_variable_names(model_description)

    unit_definitions = {}

    for unit in model_description.unitDefinitions:
        unit_definitions[unit.name] = [display_unit.name for display_unit in unit.displayUnits]

    variable_names = set()

    # assert unique variable names (FMI 1.0 spec, p. 34, FMI 2.0 spec, p. 45)
    for variable in model_description.modelVariables:
        if variable.name in variable_names:
            problems.append('Variable name "%s" (line %s) is not unique.' % (variable.name, variable.sourceline))
        variable_names.add(variable.name)

    is_fmi2 = model_description.fmiVersion == '2.0'
    is_fmi3 = model_description.fmiVersion.startswith('3.0')

    if is_fmi2 or is_fmi3:

        # assert required start values (see FMI 2.0 spec, p. 53)
        for variable in model_description.modelVariables:
            if (variable.initial in {'exact', 'approx'} or variable.causality == 'input') and variable.start is None:
                problems.append('Variable "%s" (line %s) has no start value.' % (variable.name, variable.sourceline))

        # legal combinations of causality and variability (see FMI 2.0 spec, p. 49)
        legal_combinations = {
            ('parameter', 'fixed'),
            ('parameter', 'tunable'),
            ('calculatedParameter', 'fixed'),
            ('calculatedParameter', 'tunable'),
            ('input', 'discrete'),
            ('input', 'continuous'),
            ('output', 'constant'),
            ('output', 'discrete'),
            ('output', 'continuous'),
            ('local', 'constant'),
            ('local', 'fixed'),
            ('local', 'tunable'),
            ('local', 'discrete'),
            ('local', 'continuous'),
            ('independent', 'continuous'),
        }

        if is_fmi3:
            legal_combinations.add(('input', 'clock'))
            legal_combinations.add(('output', 'clock'))

        for variable in model_description.modelVariables:
            if (variable.causality, variable.variability) not in legal_combinations:
                problems.append(
                    'The combination causality="%s" and variability="%s" in variable "%s" (line %s) is not allowed.'
                    % (variable.causality, variable.variability, variable.name, variable.sourceline))

        # check for illegal start values (see FMI 2.0.2 spec, p. 49)
        for variable in model_description.modelVariables:

            if variable.initial == 'calculated' and variable.start:
                problems.append('The variable "%s" (line %s) has initial="calculated" but provides a start value.' % (
                    variable.name, variable.sourceline))

            if variable.causality in 'independent' and variable.start:
                problems.append('The variable "%s" (line %s) has causality="independent" but provides a start value.' % (
                    variable.name, variable.sourceline))

        # validate units (see FMI 2.0 spec, p. 33ff.)
        for variable in model_description.modelVariables:

            unit = variable.unit

            if unit is None and variable.declaredType is not None:
                unit = variable.declaredType.unit

            if unit is not None and unit not in unit_definitions:
                problems.append('The unit "%s" of variable "%s" (line %s) is not defined.' % (
                    unit, variable.name, variable.sourceline))

            if variable.displayUnit is not None and variable.displayUnit not in unit_definitions[unit]:
                problems.append('The display unit "%s" of variable "%s" (line %s) is not defined.' % (
                    variable.displayUnit, variable.name, variable.sourceline))

        if validate_model_structure:
            problems += _validate_model_structure(model_description)

    return problems


def _validate_model_structure(model_description):
    problems = []

    # validate outputs
    expected_outputs = set(v for v in model_description.modelVariables if v.causality == 'output')
    outputs = set(u.variable for u in model_description.outputs)

    if expected_outputs != outputs:
        problems.append('ModelStructure/Outputs must have exactly one entry for each variable with causality="output".')

    # validate derivatives
    derivatives = set(v for v in model_description.modelVariables if v.derivative is not None)
    for i, state_derivative in enumerate(model_description.derivatives):
        if state_derivative.variable not in derivatives:
            problems.append('The variable "%s" (line %d) referenced by the continuous state derivative %d (line %d)'
                            ' must have the attribute "derivative".'
                            % (state_derivative.variable.name, state_derivative.variable.sourceline,
                               i + 1, state_derivative.sourceline))

    # validate initial unknowns
    expected_initial_unknowns = set()

    for variable in model_description.modelVariables:

        if variable.causality == 'output' and variable.initial in {'approx', 'calculated'} and not variable.clocks:
            expected_initial_unknowns.add(variable)

        if variable.causality == 'calculatedParameter':
            expected_initial_unknowns.add(variable)

    try:
        for unknown in model_description.derivatives:
            derivative = unknown.variable
            state = derivative.derivative
            for variable in [state, derivative]:
                if variable.initial in {'approx', 'calculated'}:
                    expected_initial_unknowns.add(variable)

        initial_unknowns = set(v.variable for v in model_description.initialUnknowns)

        if initial_unknowns != expected_initial_unknowns:
            expected = ', '.join(sorted(v.name for v in expected_initial_unknowns))
            actual = ', '.join(sorted(v.name for v in initial_unknowns))
            problem = ("ModelStructure/InitialUnknowns does not contain the expected set of variables." 
                       f" Expected {{{ expected }}} but was {{{ actual }}}.")
            problems.append(problem)
    except:
        pass  # this check may fail due to inconsistencies detected above

    return problems


def _validate_variable_names(model_description):
    problems = []

    if model_description.variableNamingConvention == 'flat':

        for variable in model_description.modelVariables:

            if u'\u000D' in variable.name:
                problems.append('Variable "%s" (line %s) contains an illegal carriage return character (U+000D).'
                                % (variable.name, variable.sourceline))

            if u'\u000A' in variable.name:
                problems.append('Variable "%s" (line %s) contains an illegal line feed character (U+000A).'
                                % (variable.name, variable.sourceline))

            if u'\u0009' in variable.name:
                problems.append('Variable "%s" (line %s) contains an illegal tab character (U+0009).'
                                % (variable.name, variable.sourceline))

    else:  # variableNamingConvention == structured

        from lark import Lark

        grammar = r"""
            name            : identifier | "der(" identifier ("," unsignedinteger)? ")"
            identifier      : bname arrayindices? ("." bname arrayindices?)*
            bname           : nondigit (nondigit|digit)* | qname
            nondigit        : "_" | "a".."z" | "A".."Z"
            digit           : "0".."9"
            qname           : "'" ( qchar | escape ) ( qchar | escape ) "'"
            qchar           : nondigit | digit | "!" | "#" | "$" | "%" | "&" | "(" | ")" 
                              | "*" | "+" | "," | "-" | "." | "/" | ":" | ";" | "<" | ">"
                              | "=" | "?" | "@" | "[" | "]" | "^" | "{" | "}" | "|" | "~" | " "
            escape          : "\'" | "\"" | "\?" | "\\" | "\a" | "\b" | "\f" | "\n" | "\r" | "\t" | "\v"
            arrayindices    : "[" unsignedinteger ("," unsignedinteger)* "]"
            unsignedinteger : digit+
            """

        parser = Lark(grammar, start='name')

        for variable in model_description.modelVariables:
            try:
                parser.parse(variable.name)
            except Exception as e:
                problems.append('"%s" (line %s) is not a legal variable name for naming convention "structured". %s'
                                % (variable.name, variable.sourceline, e))

    return problems
