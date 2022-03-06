from setuptools import find_packages, setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="django-apscheduler",
    version="0.6.2",
    description="APScheduler for Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/jcass77/django-apscheduler",
    author="Jarek Glowacki, Stas Kaledin, John Cass",
    author_email="jarekwg@gmail.com, staskaledin@gmail.com, john.cass77@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
    ],
    keywords="django apscheduler django-apscheduler",
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "django>=3.2",
        "apscheduler>=3.2,<4.0",
    ],
    zip_safe=False,
)
