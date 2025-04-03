# install the binaries from the wheel that matches the project version

from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
import requests
import toml
import json
import urllib.request


project_root = Path(__file__).parent.parent

with open(project_root / 'pyproject.toml', 'r') as f:
    project_data = toml.load(f)

fmpy_version = project_data['project']['version']

with urllib.request.urlopen("https://pypi.org/pypi/fmpy/json") as url:
    pypi_data = json.load(url)

wheel_url = pypi_data['releases'][fmpy_version][0]['url']

src_dir = project_root / 'src'

print(f'Downloading {wheel_url}...')

response = requests.get(wheel_url)

with ZipFile(BytesIO(response.content), 'r') as zf:

    members = []

    for name in zf.namelist():
        if name.endswith(('.exe', '.dll', '.dylib', '.so', 'server_tcp')) and not (src_dir / name).is_file():
            members.append(name)

    print(f"Extracting binaries to {src_dir}")

    for member in members:
        print(member)

    zf.extractall(src_dir, members=members)

    print(f"{len(members)} binaries installed.")
