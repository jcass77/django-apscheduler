from setuptools import find_packages, setup

setup(
    name='django_apscheduler',
    version='0.1',
    description='APScheduler for Django',
    classifiers=[
        "Development Status :: Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "License :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Framework :: Django :: 1.8",
        "Framework :: Django :: 1.9",
    ],
    keywords='django apscheduler django-apscheduler',
    url='http://github.com/sallyruthstruik/django-apscheduler',
    author='Stas Kaledin',
    author_email='staskaledin@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'django>=1.8',
        'apscheduler>=3.2.0',
    ],
    zip_safe=False
)
