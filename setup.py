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
    keywords='django oauth oauth2 oauthlib',
    url='http://github.com/jarekwg/django-apscheduler',
    author='Jarek Glowacki',
    author_email='jarekwg@gmail.com',
    license='MIT',
    packages=find_packages(),
    # test_suite='runtests',
    install_requires=[
        'django>=1.8',
        'apscheduler>=3.2.0',
    ],
    zip_safe=False
)
