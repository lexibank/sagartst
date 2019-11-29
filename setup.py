from setuptools import setup
import json


with open('metadata.json', encoding='utf-8') as fp:
    metadata = json.load(fp)


setup(
    name='lexibank_sagartst',
    version="1.1.1",
    description=metadata['title'],
    license=metadata.get('license', ''),
    url=metadata.get('url', ''),
    py_modules=['lexibank_sagartst'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'lexibank.dataset': [
            'sagartst=lexibank_sagartst:Dataset',
        ]
    },
    install_requires=[
        'pylexibank>=2.1',
    ]
)
