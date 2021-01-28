# Release procedures

Here we try to keep an up to date record of how new releases are made. This
documentation serves both as a checklist, to reduce the project's dependency on
key individuals, and as a stepping stone to more automation.

## Creating releases

1. Update changelog and commit it.

2. Bump the version number in `setup.py` and commit changes.

3. Merge the release branch (``develop`` in the example) into ``main``:

    ```
    git checkout main
    git merge --no-ff -m "Release v0.0.1" develop
    ```

4. Tag the release:

    ```
    git tag -a -m "Release v0.0.1" v0.0.1
    ```

5. Push to GitHub:

    ```
    git push --follow-tags
    ```

6. Merge ``main`` back into ``develop`` and push the branch to GitHub.

7. Create a new release on GitHub: https://github.com/jcass77/django-apscheduler/releases/new

8. Clicking "Publish" will automatically trigger a new release to get pushed to PyPi.
