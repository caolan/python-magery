from distutils.core import setup

setup(
  name = 'magery',
  packages = ['magery'],
  version = '0.0.2',
  description = 'Magery templating library',
  author = 'Caolan McMahon',
  author_email = 'caolan.mcmahon@gmail.com',
  url = 'https://github.com/caolan/python-magery',
  download_url = 'https://github.com/caolan/python-magery/tarball/0.0.2',
  keywords = ['html', 'templating', 'web'],
  classifiers=[
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 3 - Alpha',

    # Indicate who your project is intended for
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Libraries',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: MIT License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
  ],
  install_requires=['funcparserlib'],
)
