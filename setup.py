import os
import sys
import subprocess

from distutils.command.build import build
from distutils.command.build_ext import build_ext
from distutils.spawn import find_executable

from setuptools import setup
from setuptools.extension import Extension
from setuptools.command.install import install

this_dir = os.path.dirname(os.path.abspath(__file__))

jamspell = Extension(
    name='_jamspell',
    include_dirs=['.', 'jamspell'],
    sources=[
        os.path.join('jamspell', 'lang_model.cpp'),
        os.path.join('jamspell', 'spell_corrector.cpp'),
        os.path.join('jamspell', 'utils.cpp'),
        os.path.join('jamspell', 'perfect_hash.cpp'),
        os.path.join('jamspell', 'bloom_filter.cpp'),
        os.path.join('contrib', 'cityhash', 'city.cc'),
        os.path.join('contrib', 'phf', 'phf.cc'),
        os.path.join('contrib', 'sqlite', 'sqlite3.c'),
        os.path.join('jamspell.i'),
    ],
    extra_compile_args=['-std=c++11', '-O2'],
    swig_opts=['-c++'],
)

if sys.platform == 'darwin':
    jamspell.extra_compile_args.append('-stdlib=libc++')


class CustomBuild(build):
    def run(self):
        self.run_command('build_ext')
        build.run(self)


class CustomInstall(install):
    def run(self):
        self.run_command('build_ext')
        install.run(self)


class Swig3Ext(build_ext):
    @staticmethod
    def find_swig():
        swig_binary = find_executable('swig3.0') or find_executable('swig')
        assert swig_binary is not None
        assert subprocess.check_output([swig_binary, "-version"]).find(b'SWIG Version 3') != -1
        return swig_binary


VERSION = '0.0.12'

setup(
    name='jamspell',
    version=VERSION,
    author='Filipp Ozinov',
    author_email='fippo@mail.ru',
    url='https://github.com/bakwc/JamSpell',
    download_url='https://github.com/bakwc/JamSpell/tarball/' + VERSION,
    description='spell checker',
    long_description='context-based spell checker',
    keywords=['nlp', 'spell', 'spell-checker', 'jamspell'],
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
    ],
    py_modules=['jamspell'],
    ext_modules=[jamspell],
    zip_safe=False,
    cmdclass={
        'build': CustomBuild,
        'install': CustomInstall,
        'build_ext': Swig3Ext,
    },
    include_package_data=True,
    install_requires=['hunspell~=0.5.5', 'langdetect==1.0.7', 'pytest~=6.2.2', 'scipy~=1.6.1',
                      'kenlm @ git+https://github.com/kpu/kenlm.git@master#egg=kenlm'],
    dependency_links=["git+https://github.com/kpu/kenlm.git@master#egg=kenlm"]
)
