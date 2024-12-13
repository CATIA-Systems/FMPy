# download and install the binaries from the latest wheel

from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
import requests

src_dir = Path(__file__).absolute().parent.parent / 'src'

url = 'https://files.pythonhosted.org/packages/d0/86/87a735aa1177be40e0fdc01ba87509eec6f5a80d7738cd84a732ba3bae23/FMPy-0.3.22-py3-none-any.whl'

print(f'Downloading {url}...')

response = requests.get(url)

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
