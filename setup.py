""" Setup for the CEDA Account Django application. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from setuptools import setup, find_packages


with open("README.md") as readme_file:
    long_description = readme_file.read()


setup(
    name = "ceda-account",
    version = "0.1.0",
    description = "Django application for registering and managing CEDA users.",
    author = "William Tucker",
    author_email = "william.tucker@stfc.ac.uk",
    maintainer = "William Tucker",
    maintainer_email = "william.tucker@stfc.ac.uk",
    url = "https://github.com/cedadev/ceda-account",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    license = "BSD - See ceda_example/LICENSE file for details",
    packages = find_packages(),
    install_requires = [
        "django",
        "django-allauth",
        "django-crispy-forms",
        "fwtheme-django",
        "fwtheme-django-ceda-serv",
    ],
    classifiers = [
        "Development Status :: 1 - Planning",
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
