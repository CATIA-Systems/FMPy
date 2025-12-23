from lxml import etree

from fmpy import read_model_description
from fmpy.model_description import write_model_description


def test_write_model_description(reference_fmus_dist_dir, reference_fmus_repo_dir, work_dir):

    model_description = read_model_description(
        reference_fmus_dist_dir / "3.0" / "BouncingBall.fmu"
    )

    path = work_dir / "modelDescription.xml"

    write_model_description(model_description, path)

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
