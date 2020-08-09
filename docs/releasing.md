# Release procedures

Here we try to keep an up to date record of how new releases are made. This
documentation serves both as a checklist, to reduce the project's dependency on
key individuals, and as a stepping stone to more automation.

## Creating releases

1. Update changelog and bump the version number in `setup.py`. Commit changes.

2. Merge the release branch (``develop`` in the example) into master:

        git checkout master
        git merge --no-ff -m "Release v0.3.0" develop

3. Tag the release:

        git tag -a -m "Release v0.3.0" v0.3.0

4. Push to GitHub:

        git push --follow-tags

5. Merge ``master`` back into ``develop`` and push the branch to GitHub.

6. Document the release on GitHub by clicking on the 'Releases' link on the landing page,
   and editing the tag that was just created. Set both the tag version and release title
   to "v0.3.0".
