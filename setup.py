from setuptools import setup, find_packages

setup(
    name='thordata_sdk',
    version='0.2.2',  # Bump version due to breaking auth changes
    packages=find_packages(include=['thordata_sdk', 'thordata_sdk.*']),
    install_requires=[
        'requests>=2.25.0',  # Standard synchronous HTTP
        'aiohttp>=3.8.0',    # Async HTTP for high concurrency
        # Removed 'pydantic' as it is not currently used in the source code.
        # Keep dependencies minimal to avoid conflicts for users.
    ],
    author='Thordata Developer Team',
    author_email='support@thordata.com', # Added email field
    description='The official Python SDK for Thordata Proxy & Scraper Infrastructure.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    license='Apache License 2.0',
    url='https://github.com/Thordata/thordata-python-sdk',
    project_urls={
        "Bug Tracker": "https://github.com/Thordata/thordata-python-sdk/issues",
        "Documentation": "https://github.com/Thordata/thordata-python-sdk#readme",
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3.8',
)