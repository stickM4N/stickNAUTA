from setuptools import (setup, find_packages)

with open('README.md', 'r', encoding='utf-8') as file:
    readme = file.read()
with open('requirements.txt', 'r', encoding='utf-8') as file:
    requirements = [requirement[:-1] if requirement.endswith('\n') else requirement for requirement in file]

setup(
    script_name='setup.py',
    name='stickNAUTA',
    version='2.0.2',
    author='stickM4N',
    author_email='jcgalindo.jcgh@gmail.com',
    license='MIT',
    description='Simple managing interface for ETECSA Nauta.',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/stickM4N/stickNAUTA',
    project_urls={},
    download_url=f'https://pypi.org/project/stickNAUTA',
    keywords='python nauta etecsa',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP :: Session',
        'Topic :: Internet :: WWW/HTTP :: Site Management'
    ],
    install_requires=requirements,
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.7',
)
