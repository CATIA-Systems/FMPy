from lxml.etree import SubElement

from fmpy import read_model_description
from fmpy.model_description import ModelDescription, DisplayUnit
from lxml import etree
from pathlib import Path


def write_fmi3_model_description(model_description: ModelDescription, path: Path):

    def to_literal(value):
        if value is None:
            return None
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def set_attributes(element, object, attributes):
        for attribute_name, default_value in attributes:
            value = getattr(object, attribute_name)
            if value != default_value:
                element.set(attribute_name, to_literal(value))

    root = etree.Element("fmiModelDescription")

    # basic attributes
    for attr in (
        "fmiVersion",
        "modelName",
        "instantiationToken",
        "description",
        "author",
        "version",
        "copyright",
        "license",
        "generationTool",
        "generationDateAndTime",
        "variableNamingConvention",
    ):
        val = getattr(model_description, attr, None)
        if val is not None:
            root.set(attr, to_literal(val))

    implementation_attributes = [
        ("modelIdentifier", None),
        ("needsExecutionTool", False),
        ("canBeInstantiatedOnlyOncePerProcess", False),
        ("canGetAndSetFMUState", False),
        ("canSerializeFMUState", False),
        ("providesDirectionalDerivative", False),
        ("providesAdjointDerivatives", False),
        ("providesPerElementDependencies", False),
    ]

    if model_description.modelExchange is not None:
        ModelExchange = SubElement(root, "ModelExchange")
        set_attributes(ModelExchange, model_description.modelExchange, implementation_attributes + [
            ("needsCompletedIntegratorStep", False),
            ("providesEvaluateDiscreteStates", False),
        ])

    if model_description.modelExchange is not None:
        CoSimulation = SubElement(root, "CoSimulation")
        set_attributes(CoSimulation, model_description.coSimulation, implementation_attributes + [
            ("canHandleVariableCommunicationStepSize", False),
            ("fixedInternalStepSize", None),
            ("maxOutputDerivativeOrder", False),
            ("recommendedIntermediateInputSmoothness", False),
            ("canInterpolateInputs", False),
            ("providesIntermediateUpdate", False),
            ("mightReturnEarlyFromDoStep", False),
            ("canReturnEarlyAfterIntermediateUpdate", False),
            ("hasEventMode", False),
            ("providesEvaluateDiscreteStates", False),
        ])

    if model_description.unitDefinitions:
        UnitDefinitions = SubElement(root, "UnitDefinitions")
        for unit in model_description.unitDefinitions:
            Unit = SubElement(UnitDefinitions, "Unit")
            Unit.set("name", unit.name)
            BaseUnit = SubElement(Unit, "BaseUnit")
            set_attributes(
                BaseUnit,
                unit.baseUnit,
                [
                    ("kg", 0),
                    ("m", 0),
                    ("s", 0),
                    ("A", 0),
                    ("K", 0),
                    ("mol", 0),
                    ("cd", 0),
                    ("rad", 0),
                    ("factor", 1.0),
                    ("offset", 0.0),
                ],
            )
            for display_unit in unit.displayUnits:
                DisplayUnit = SubElement(Unit, "DisplayUnit")
                set_attributes(DisplayUnit, display_unit, [("name", None), ("factor", 1.0), ("offset", 0.0)])

    if model_description.typeDefinitions:
        TypeDefintions = SubElement(root, "TypeDefinitions")
        for type_defintion in model_description.typeDefinitions:
            TypeDefinition = SubElement(
                TypeDefintions, type_defintion.type + "Type"
            )
            set_attributes(
                TypeDefinition,
                type_defintion,
                [
                    ("name", None),
                    ("description", None),
                    ("quantity", None),
                    ("unit", None),
                    ("displayUnit", None),
                    ("relativeQuantity", None),
                    ("min", None),
                    ("max", None),
                    ("nominal", None),
                    ("nominal", None),
                    ("unbounded", None),
                ],
            )

    if model_description.logCategories:
        LogCategories = SubElement(root, "LogCategories")
        for category in model_description.logCategories:
            Category = SubElement(LogCategories, "Category")
            set_attributes(Category, category, [("name", None), ("description", None)])

    if model_description.defaultExperiment is not None:
        DefaultExperiment = SubElement(root, "DefaultExperiment")
        set_attributes(DefaultExperiment, model_description.defaultExperiment, [("startTime", None), ("stopTime", None), ("stepSize", None)])

    ModelVariables = SubElement(root, "ModelVariables")

    for variable in model_description.modelVariables:
        if variable.alias is not None:
            continue

        ModelVariable = SubElement(ModelVariables, variable.type)

        set_attributes(
            ModelVariable,
            variable,
            [
                ("name", None),
                ("valueReference", None),
                ("causality", None),
                ("start", None),
                ("variability", None),
                ("initial", None),
                ("declaredType", None),
                ("derivative", None),
                ("description", None),
            ],
        )

        if variable.derivative is not None:
            ModelVariable.set("derivative", str(variable.derivative.valueReference))

        if variable.declaredType is not None:
            ModelVariable.set("declaredType", variable.declaredType.name)

        for alias in variable.aliases:
            Alias = SubElement(ModelVariable, "Alias")
            Alias.set("name", alias.name)
            Alias.set("description", alias.description)
            Alias.set("displayUnit", alias.displayUnit)

    ModelStructure = SubElement(root, "ModelStructure")

    for element_name, unknowns in [
        ("Output", model_description.outputs),
        ("ContinuousStateDerivative", model_description.derivatives),
        ("InitialUnknown", model_description.initialUnknowns),
        ("EventIndicator", model_description.eventIndicators),
    ]:
        for unknown in unknowns:
            Unknown = SubElement(ModelStructure, element_name)
            Unknown.set("valueReference", str(unknown.variable.valueReference))
            if unknown.dependencies is not None:
                Unknown.set(
                    "dependencies",
                    " ".join(
                        map(lambda v: str(v.valueReference), unknown.dependencies)
                    ),
                )
            if unknown.dependenciesKind is not None:
                Unknown.set("dependenciesKind", " ".join(unknown.dependenciesKind))

    tree = etree.ElementTree(root)

    tree.write(path, encoding="utf-8", xml_declaration=True, pretty_print=True)


def test_read_model_description(reference_fmus_repo_dir):
    read_model_description(
        # str(reference_fmus_repo_dir / "BouncingBall" / "FMI3.xml"),
        r"E:\WS\FMPy\tests\work\modelDescription.xml",
        validate_model_structure=True
    )

def test_write_model_description(reference_fmus_dist_dir, reference_fmus_repo_dir, work_dir):

    model_description = read_model_description(
        reference_fmus_dist_dir / "3.0" / "BouncingBall.fmu"
    )

    path = work_dir / "modelDescription.xml"

    write_fmi3_model_description(model_description, path)

    read_model_description(
        str(path),
        validate=True,
        validate_model_structure=True,
        validate_variable_names=True,
    )

    xml_a = etree.parse(path)
    xml_b = etree.parse(reference_fmus_repo_dir / "BouncingBall" / "FMI3.xml")

    def assert_attributes_equal(parsed, reference, xpath):
        elements_a = parsed.xpath(xpath)
        elements_b = reference.xpath(xpath)
        assert len(elements_a) == len(elements_b)
        for a, b in zip(elements_a, elements_b):
            assert a.attrib == b.attrib, f"{a.attrib} != {b.attrib}"

    assert_attributes_equal(xml_a, xml_b, ".//ModelExchange")
    assert_attributes_equal(xml_a, xml_b, ".//CoSimulation")
    assert_attributes_equal(xml_a, xml_b, ".//UnitDefinitions/Unit")
    assert_attributes_equal(xml_a, xml_b, ".//UnitDefinitions/Unit/BaseUnit")
    assert_attributes_equal(xml_a, xml_b, ".//TypeDefinitions/*")
    assert_attributes_equal(xml_a, xml_b, ".//LogCategories/*")
    assert_attributes_equal(xml_a, xml_b, ".//DefaultExperiment")
