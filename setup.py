from setuptools import setup, find_packages

setup(
    name='thordata-sdk',  # pip install thordata-sdk
    version='0.1.0',     # 初始版本号
    packages=find_packages(include=['thordata_sdk', 'thordata_sdk.*']), # 确保包含 thordata_sdk
    install_requires=[
        'requests',      # 依赖 requests 库处理 HTTP 请求
        'pydantic',      # 依赖 pydantic 库用于数据结构（AI 友好）
        'aiohttp',       # 依赖 aiohttp 库用于异步请求（高并发）
    ],
    author='Thordata Developer Team',
    description='The official Python SDK for Thordata Proxy Infrastructure.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    license='Apache License 2.0', # 根据你的 LICENSE 文件，使用 Apache 2.0
    url='https://github.com/Thordata/thordata-python-sdk',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License', # 对应 Apache 2.0
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3.8',
)