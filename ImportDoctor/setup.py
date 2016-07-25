from setuptools import setup, find_packages
# TO UPDATE:
# - Change version number
# - python setup.py register sdist upload

setup(
    name='ImportDoctor',
    version='1.2.2.2',
    description='Python file formatter for import statements',
    author='Ted Tenedorio',
    author_email='tedtenedorio@gmail.com',
    url='https://github.com/freetheinterns/import_doctor',
    entry_points={
        'console_scritps': [
            'ImportDoctor = ImportDoctor:main'
        ]
    },
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Specify the Python versions you support here.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='import tool format development',
    packages=find_packages(exclude=['prefs'])
#     packages=find_packages(exclude=['prefs', 'dist', 'ImportDoctor.egg-info'])
)
