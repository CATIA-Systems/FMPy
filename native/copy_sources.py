# copy the sources of the Container FMU
import shutil
from pathlib import Path

root = Path(__file__).absolute().parent

for file in [
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack.h',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-common.c',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-common.h',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-expect.c',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-expect.h',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-node.c',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-node.h',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-platform.c',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-platform.h',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-reader.c',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-reader.h',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-writer.c',
    root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-writer.h',
    root / 'thirdparty' / 'Reference-FMUs' / 'src' / 'FMI.c',
    root / 'thirdparty' / 'Reference-FMUs' / 'include' / 'FMI.h',
    root / 'thirdparty' / 'Reference-FMUs' / 'src' / 'FMI2.c',
    root / 'thirdparty' / 'Reference-FMUs' / 'include' / 'FMI2.h',
    root / 'src' / 'fmucontainer' / 'fmi2Functions.c',
    root / 'src' / 'fmucontainer' / 'fmi3Functions.c',
    root / 'src' / 'fmucontainer' / 'FMUContainer.c',
    root / 'src' / 'fmucontainer' / 'FMUContainer.h',
]:
    shutil.copyfile(src=file, dst=root / '..' / 'src' / 'fmpy' / 'fmucontainer' / 'sources' / file.name)
