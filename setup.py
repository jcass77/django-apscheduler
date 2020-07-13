from setuptools import find_packages, setup

setup(
    name='django-apscheduler',
    version='0.3.1',
    description='APScheduler for Django',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
    ],
    keywords='django apscheduler django-apscheduler',
    url='http://github.com/jarekwg/django-apscheduler',
    author='Jarek Glowacki, Stas Kaledin',
    author_email='jarekwg@gmail.com, staskaledin@gmail.com',
    license='MIT',
    packages=find_packages(
        exclude=("tests", )
    ),
    install_requires=[
        'django>=1.11',
        'apscheduler>=3.2.0',
    ],
    zip_safe=False
)
