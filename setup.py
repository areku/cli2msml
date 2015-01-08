from setuptools import setup

setup(
    name='cli2msml',
    version='0.1-alpha',
    url='https://github.com/CognitionGuidedSurgery/cli2msml',
    license='GPL v3',
    py_modules=['cli2msml'],
    author='Alexander Weigl',
    author_email='uiduw@student.kit.edu',
    description='Converter for CLI apps into MSML Operators',
    install_requires=['cliff', 'click', 'path.py', 
        'colorama', 'pyyaml', 'jinja2'],
    entry_points={
        'console_scripts': [
            'cli2msml=cli2msml:cli'
        ],
    },
    classifiers=(
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)", "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Utilities",
    )
)
