import os
import shutil
import zipfile
from pathlib import Path
from shutil import make_archive, unpack_archive

root = Path(__file__).parent
temp = root / 'wheels' / 'temp'
merged = root / 'wheels' / 'merged'


if temp.exists():
    shutil.rmtree(temp)

os.makedirs(temp)

if merged.exists():
    shutil.rmtree(merged)

os.makedirs(merged)

wheels = []

for dirpath, _, filenames in os.walk(root / 'wheels'):
    for filename in filenames:
        if filename.endswith('.whl'):
            wheels.append(root / dirpath / filename)

records = set()

for wheel in wheels:
    with zipfile.ZipFile(wheel, 'r') as archive:
        for info in archive.filelist:
            if info.filename.endswith('RECORD'):
                record = info.filename
                break
        records.update(archive.read(record).split(b'\n'))
        archive.extractall(temp)

    unpack_archive(wheel, temp, 'zip')

with open(temp / record, 'w') as record:
    lines = [line.decode('utf-8') for line in records]
    lines.sort()
    lines = list(filter(lambda line: line != "", lines))
    record.writelines('\n'.join(lines))

make_archive(str(merged / wheels[0].stem), 'zip', temp)
os.rename(merged / (wheels[0].stem + '.zip'), merged / wheels[0].name)
