""" Setup for the CEDA Services Portal Django application. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from setuptools import setup, find_packages

with open("README.md") as readme_file:
    long_description = readme_file.read()


setup(
    name = "ceda-services-portal",
    version = "0.2.0",
    description = "Django application for registering and managing CEDA users.",
    author = "William Tucker",
    author_email = "william.tucker@stfc.ac.uk",
    maintainer = "William Tucker",
    maintainer_email = "william.tucker@stfc.ac.uk",
    url = "https://github.com/cedadev/ceda-services-portal",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    license = "BSD - See ceda_example/LICENSE file for details",
    packages = find_packages(),
    install_requires = [
        "django",
        "python-dateutil",
        "django-crispy-forms",
        "django-widget-tweaks",
        "django-countries",
        "fwtheme-django",
        "fwtheme-django-ceda-serv",
        "mozilla-django-oidc",
        "unidecode",
        "psycopg2-binary",
    ],
    classifiers = [
        "Development Status :: 2 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    zip_safe = False,
)
