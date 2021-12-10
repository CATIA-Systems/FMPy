""" Validation of the modelDescription.xml """

from typing import List

from fmpy.model_description import ModelDescription


def validate_fmu(filename: str) -> List[str]:
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
    import os
    import zipfile

    problems = []

    # check file paths
    if isinstance(filename, str) and os.path.isfile(filename):
        with zipfile.ZipFile(filename, 'r') as zf:
            for file in zf.filelist:
                if '\\' in file.orig_filename:
                    problems.append(f'The file path "{file.orig_filename}" contains a backslash.')

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


def validate_model_description(model_description: ModelDescription, validate_variable_names: bool = False, validate_model_structure: bool = False) -> List[str]:

    problems = []

    if validate_variable_names:
        problems += _validate_variable_names(model_description)

    unit_definitions = {}

    for unit in model_description.unitDefinitions:
        unit_definitions[unit.name] = [display_unit.name for display_unit in unit.displayUnits]

    variable_names = set()

    # assert unique variable names (FMI 1.0 spec, p. 34, FMI 2.0 spec, p. 45)
    for v in model_description.modelVariables:
        if v.name in variable_names:
            problems.append(f'The variable name "{v.name}" (line {v.sourceline}) is not unique.')
        variable_names.add(v.name)

    is_fmi2 = model_description.fmiVersion == '2.0'
    is_fmi3 = model_description.fmiVersion.startswith('3.0')

    if is_fmi2 or is_fmi3:

        # assert required start values (see FMI 2.0 spec, p. 53)
        for v in model_description.modelVariables:
            if v.type != 'Clock' and (v.initial in {'exact', 'approx'} or v.causality == 'input') and v.start is None:
                problems.append(f'Variable "{v.name}" (line {v.sourceline}) has no start value.')

        # assert that initial is not set for input and independent variables (see FMI 2.0 spec, p. 49)
        for v in model_description.modelVariables:
            if v.causality in {'input', 'independent'} and v.initial is not None:
                problems.append(f'Variable "{v.name}" (line {v.sourceline}) " has causality "{v.causality}" but defines a intial "{v.initial}".')

        # legal combinations of causality and variability (see FMI 2.0 spec, p. 49)
        legal_combinations = {
            ('parameter', 'fixed'),
            ('parameter', 'tunable'),
            ('calculatedParameter', 'fixed'),
            ('calculatedParameter', 'tunable'),
            ('structuralParameter', 'fixed'),
            ('structuralParameter', 'tunable'),
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

        for v in model_description.modelVariables:
            if (v.causality, v.variability) not in legal_combinations:
                problems.append(f'The combination causality="{v.causality}" and variability="{v.variability}" '
                                f'in variable "{v.name}" (line {v.sourceline}) is not allowed.')

        # check for illegal start values (see FMI 2.0.2 spec, p. 49)
        for v in model_description.modelVariables:

            if v.initial == 'calculated' and v.start:
                problems.append(f'The variable "{v.name}" (line {v.sourceline}) has initial="calculated" but provides a start value.')

            if v.causality in 'independent' and v.start:
                problems.append(f'The variable "{v.name}" (line {v.sourceline}) has causality="independent" but provides a start value.')

        # validate units (see FMI 2.0 spec, p. 33ff.)
        for v in model_description.modelVariables:

            unit = v.unit

            if unit is None and v.declaredType is not None:
                unit = v.declaredType.unit

            if unit is not None and unit not in unit_definitions:
                problems.append(f'The unit "{unit}" of variable "{v.name}" (line {v.sourceline}) is not defined.')

            if v.displayUnit is not None and v.displayUnit not in unit_definitions[unit]:
                problems.append(f'The display unit "{v.displayUnit}" of variable "{v.name}" (line {v.sourceline}) is not defined.')

        if validate_model_structure:
            problems += _validate_model_structure(model_description)

    if is_fmi3:

        # assert independent variable
        if sum(v.causality == 'independent' for v in model_description.modelVariables) != 1:
            problems.append("Exactly one independent variable must be defined.")

        # assert unique value references
        variables = dict()
        
        for v in model_description.modelVariables:
            if v.valueReference in variables:
                p = variables[v.valueReference]
                problems.append(f'Variable "{v.name}" (line {v.sourceline}) has the same value reference as variable "{p.name}" (line {p.sourceline}).')
            else:
                variables[v.valueReference] = v

    return problems


def _validate_model_structure(model_description: ModelDescription) -> List[str]:

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
            problems.append(f'The variable "{state_derivative.variable.name}" (line {state_derivative.variable.sourceline}) '
                            f'referenced by the continuous state derivative {i + 1} (line {state_derivative.sourceline}) '
                            f'must have the attribute "derivative".')

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


def _validate_variable_names(model_description: ModelDescription) -> List[str]:

    problems = []

    if model_description.variableNamingConvention == 'flat':

        for variable in model_description.modelVariables:

            if u'\u000D' in variable.name:
                problems.append(f'Variable "{variable.name}" (line {variable.sourceline}) contains an illegal carriage return character (U+000D).')

            if u'\u000A' in variable.name:
                problems.append(f'Variable "{variable.name}" (line {variable.sourceline}) contains an illegal line feed character (U+000A).')

            if u'\u0009' in variable.name:
                problems.append(f'Variable "{variable.name}" (line {variable.sourceline}) contains an illegal tab character (U+0009).')

    else:  # variableNamingConvention == structured

        from lark import Lark

        grammar = r"""
            name            : identifier | "der(" identifier ("," unsignedinteger)? ")"
            identifier      : bname arrayindices? ("." bname arrayindices?)*
            bname           : nondigit (nondigit|digit)* | qname
            nondigit        : "_" | "a".."z" | "A".."Z"
            digit           : "0".."9"
            qname           : "'" ( qchar | escape )+ "'"
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
