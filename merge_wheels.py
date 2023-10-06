import os
import shutil
import zipfile
from pathlib import Path
from shutil import make_archive, unpack_archive

root = Path(__file__).parent
merge = root / 'merge'
merged = root / 'merged'


if merge.exists():
    shutil.rmtree(merge)

os.makedirs(merge)

if merged.exists():
    shutil.rmtree(merged)

os.makedirs(merged)

wheels = []

for dirpath, dirnames, filenames in os.walk(root):
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
        archive.extractall(merge)

    unpack_archive(wheel, merge, 'zip')

with open(merge / record, 'w') as record:
    lines = [line.decode('utf-8') for line in records]
    lines.sort()
    record.writelines('\n'.join(lines))

make_archive(merged / wheels[0].stem, 'zip', merge)
os.rename(merged / (wheels[0].stem + '.zip'), merged / wheels[0].name)
