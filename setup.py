"""
Setup configuration for Lista de Presentes de Natal
"""
import os
from pathlib import Path
from setuptools import setup, find_packages

# Ler versão do arquivo VERSION
VERSION_FILE = Path(__file__).parent / 'VERSION'
with open(VERSION_FILE, 'r', encoding='utf-8') as f:
    version = f.read().strip()

# Ler README para long_description
README_FILE = Path(__file__).parent / 'README.md'
with open(README_FILE, 'r', encoding='utf-8') as f:
    long_description = f.read()

# Ler requirements
REQUIREMENTS_FILE = Path(__file__).parent / 'requirements.txt'
with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='lista-presentes-natal',
    version=version,
    description='Aplicação web Django para gerenciar listas de presentes de Natal em família',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Maxwell da Silva Oliveira',
    author_email='maxwbh@gmail.com',
    url='https://github.com/Maxwbh/Lista_de_Presentes',
    project_urls={
        'Bug Reports': 'https://github.com/Maxwbh/Lista_de_Presentes/issues',
        'Source': 'https://github.com/Maxwbh/Lista_de_Presentes',
        'Documentation': 'https://github.com/Maxwbh/Lista_de_Presentes#readme',
        'Demo': 'https://lista-presentes-0hbp.onrender.com',
        'Changelog': 'https://github.com/Maxwbh/Lista_de_Presentes/blob/main/CHANGELOG.md',
    },
    license='MIT',
    packages=find_packages(exclude=['tests*', 'docs*']),
    include_package_data=True,
    install_requires=requirements,
    python_requires='>=3.11',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 5.0',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Portuguese (Brazilian)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Office/Business',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    keywords=[
        'django',
        'wishlist',
        'christmas',
        'natal',
        'presentes',
        'gift',
        'lista',
        'pwa',
        'web-app',
        'family',
        'familia',
    ],
    entry_points={
        'console_scripts': [
            'lista-presentes=manage:main',
        ],
    },
    zip_safe=False,
)
