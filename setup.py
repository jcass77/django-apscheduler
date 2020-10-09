from setuptools import find_packages, setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="django-apscheduler",
    version="0.4.2",
    description="APScheduler for Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/jarekwg/django-apscheduler",
    author="Jarek Glowacki, Stas Kaledin",
    author_email="jarekwg@gmail.com, staskaledin@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    keywords="django apscheduler django-apscheduler",
    packages=find_packages(exclude=("tests",)),
    install_requires=["django>=2.2", "apscheduler>=3.2",],
    zip_safe=False,
)
