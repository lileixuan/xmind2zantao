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
               "Operating System :: OS Independent"] + [
                  ("Programming Language :: Python :: %s" % x) for x in "2.7".split()]

requires = [
    'xmindparser',
    'requests<2.28',
    'MarkupSafe==1.1.1',
    'flask==1.1.4',
    'arrow==0.17.0',
    'gunicorn==19.10.0',
]


def main():
    setup(
        name="xmind2zantao",
        description="Convert xmind to zantao csv",
        url='https://github.com/lileixuan/xmind2zantao',
        keywords="xmind zantao import converter testing testcase",
        classifiers=classifiers,
        version="2.0.0",
        author="LileiXuan",
        author_email="lileixuan@gmail.com",
        packages=find_packages(exclude=['tests', 'tests.*']),
        package_data={  # custom
            '': ['README.md'],
            'xmind2zantao_web': ['static/*', 'static/css/*', 'static/guide/*', 'templates/*', 'schema.sql'],
        },
        install_requires=requires,
        long_description=open('README.md').read(),
        long_description_content_type='text/markdown',
        zip_safe=False
    )


if __name__ == "__main__":
    main()
