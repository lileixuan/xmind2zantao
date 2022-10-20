"""
Documentation
-------------
xmind2zantao is a tool to help you convert xmind file to zantao recognized csv files

"""
from os import path

from setuptools import setup, find_packages

current_dir = path.abspath(path.dirname(__file__))
long_description = __doc__

classifiers = ["License :: OSI Approved :: MIT License",
               "Topic :: Software Development",
               "Topic :: Utilities",
               "Operating System :: Microsoft :: Windows",
               "Operating System :: MacOS :: MacOS X"] + [
                  ("Programming Language :: Python :: %s" % x) for x in "2.7".split()]

requires = [
    'xmindparser',
    'requests<2.28'
]


def main():
    setup(
        name="xmind2zantao",
        description="Convert xmind to zantao csv",
        keywords="xmind zantao import converter testing testcase",
        classifiers=classifiers,
        version="1.0.0",
        author="LileiXuan",
        author_email="lileixuan@gmail.com",
        packages=find_packages(exclude=['tests', 'tests.*']),
        package_data={},
        install_requires=requires,
        zip_safe=False
    )


if __name__ == "__main__":
    main()
