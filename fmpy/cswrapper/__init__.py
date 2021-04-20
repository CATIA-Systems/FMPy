

def add_cswrapper(filename, outfilename=None):

    from fmpy import read_model_description, extract, sharedLibraryExtension, platform, __version__
    from lxml import etree
    import os
    from shutil import copyfile, rmtree

    if outfilename is None:
        outfilename = filename

    model_description = read_model_description(filename)

    if model_description.fmiVersion != '2.0':
        raise Exception("%s is not an FMI 2.0 FMU." % filename)

    if model_description.modelExchange is None:
        raise Exception("%s does not support Model Exchange." % filename)

    unzipdir = extract(filename)

    xml = os.path.join(unzipdir, 'modelDescription.xml')

    tree = etree.parse(xml)

    root = tree.getroot()

    # update description
    generation_tool = root.attrib.get('generationTool', 'Unknown') + " with FMPy %s Co-Simulation wrapper" % __version__
    root.attrib['generationTool'] = generation_tool

    # remove any existing <CoSimulation> element
    for e in root.findall('CoSimulation'):
        root.remove(e)

    for i, child in enumerate(root):
        if child.tag == 'ModelExchange':
            break

    model_identifier = '%s_%s_%s' % (model_description.modelExchange.modelIdentifier,
                                     model_description.numberOfContinuousStates,
                                     model_description.numberOfEventIndicators)

    e = etree.Element("CoSimulation")
    e.attrib['modelIdentifier'] = model_identifier
    root.insert(i + 1, e)

    tree.write(xml, pretty_print=True, encoding='utf-8')

    shared_library = os.path.join(os.path.dirname(__file__), 'cswrapper' + sharedLibraryExtension)
    license_file = os.path.join(os.path.dirname(__file__), 'license.txt')

    licenses_dir = os.path.join(unzipdir, 'documentation', 'licenses')

    if not os.path.isdir(licenses_dir):
        os.mkdir(licenses_dir)

    copyfile(src=shared_library, dst=os.path.join(unzipdir, 'binaries', platform, model_identifier + sharedLibraryExtension))
    copyfile(license_file, os.path.join(unzipdir, 'documentation', 'licenses', 'fmpy-cswrapper.txt'))

    create_zip_archive(outfilename, unzipdir)

    rmtree(unzipdir, ignore_errors=True)


def create_zip_archive(filename, source_dir):

    import zipfile
    import os

    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        base_path = os.path.normpath(source_dir)
        for dirpath, dirnames, filenames in os.walk(source_dir):
            for name in sorted(dirnames):
                path = os.path.normpath(os.path.join(dirpath, name))
                zf.write(path, os.path.relpath(path, base_path))
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                if os.path.isfile(path):
                    zf.write(path, os.path.relpath(path, base_path))
