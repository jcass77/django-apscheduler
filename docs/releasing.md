# Release procedures

Here we try to keep an up to date record of how new releases are made. This
documentation serves both as a checklist, to reduce the project's dependency on
key individuals, and as a stepping stone to more automation.

## Creating releases

1. Update changelog and commit it.

2. Bump the version number in `setup.py` and commit changes.

3. Push to GitHub.

4. Create a new release on GitHub: https://github.com/jarekwg/django-apscheduler/releases/new

    - Set both tag version and release title to the semantic version number (e.g. "0.4.1") 
    - Clicking "Publish" will automatically trigger a new release to get pushed to PyPi.