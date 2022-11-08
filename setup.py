""" Setup for the CEDA Portal Django application. """

__author__ = "William Tucker"
__date__ = "2019-08-28"
__copyright__ = "Copyright 2019 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level directory"


from setuptools import find_packages, setup

with open("README.md") as readme_file:
    long_description = readme_file.read()

setup(
    name="ceda-services-portal",
    version="0.2.0",
    description="Django application for registering and managing CEDA users.",
    author="William Tucker",
    author_email="william.tucker@stfc.ac.uk",
    maintainer="William Tucker",
    maintainer_email="william.tucker@stfc.ac.uk",
    url="https://github.com/cedadev/ceda-services-portal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="BSD - See ceda_example/LICENSE file for details",
    packages=find_packages(),
    install_requires=[
        "Django>=3.2,<3.3",
        "crypto-cookie @ git+https://github.com/cedadev/crypto-cookie.git@b92dd9e6cc910d48d9380222c9273c8929666980",
        "dj-security-middleware @ git+https://github.com/cedadev/dj-security-middleware.git@a274146198848db1684c366400d57376509b52d9",
        "django-cookie-law==2.1.0",
        "django-countries>=7.2.1,<7.3.0",
        "django-crispy-forms>=1.14.0,<2.0.0",
        "django-markdown-deux>=1.0.5,<2.0.0",
        "django-oidc-extras @ git+https://github.com/cedadev/django-oidc-extras.git@7865641af8e0886bca244e2fc9ab27221f518ef8",
        "django-polymorphic>=3.1.0,<4.0.0",
        "django-widget-tweaks>=1.4.12,<2.0.0",
        "djangorestframework>=3.13.1,<4.0.0",
        "fwtheme-django @ git+https://github.com/cedadev/fwtheme-django.git@1.0.1",
        "fwtheme-django-ceda-serv @ git+https://github.com/cedadev/fwtheme-django-ceda-serv.git@1.5.0",
        "importlib-metadata>=4.11.0,<5.0.0",
        "jasmin-django-utils @ git+https://github.com/cedadev/jasmin-django-utils.git@v1.0.6",
        "jasmin-ldap @ git+https://github.com/cedadev/jasmin-ldap.git@v1.0.0",
        "jasmin-ldap-django @ git+https://github.com/cedadev/jasmin-ldap-django.git@v1.0.1",
        "jasmin-metadata @ git+https://github.com/cedadev/jasmin-metadata.git@v1.0.0",
        "jasmin-notifications @ git+https://github.com/cedadev/jasmin-notifications.git@v1.1.0",
        "jasmin-services[keycloak] @ git+https://github.com/cedadev/jasmin-services.git@8faa8324c71d4e5bb38f612c27a9682ccaab13dd",
        "mozilla-django-oidc>=2.0.0,<3.0.0",
        "oauthlib>=3.2.0,<4.0.0",
        "pika>=1.2.0,<2.0.0",
        "psycopg2-binary>=2.9.3,<3.0.0",
        "python-dateutil>=2.8.2,<3.0.0",
        "requests-oauthlib>=1.3.1,<2.0.0",
    ],
    classifiers=[
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
    zip_safe=False,
)
