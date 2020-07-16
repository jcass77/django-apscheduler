# Changelog

This changelog is used to track all major changes to django_apscheduler.

## v0.4.0 (UNRELEASED)

**Enhancements**

- Drop support for Python 2.7, convert codebase to Python 3.6+.
- CI: drop coverage for Python 2.7 and Django <= 2.1, which are no longer maintained upstream.
- CI: add coverage for Python 3.7 and 3.8, as well as Django long term support (LTS) and the latest released versions.
- CI: un-pin dependency on agronholm/apscheduler#149, which has since been merged and released upstream.
- Rename Django `test_settings.py` file to prevent collision with actual test scripts.
- Clean up unused dependencies / update dependencies to latest available versions.
- Switch to Black code formatting.
- Align package layout with official [Django recommendations](https://docs.djangoproject.com/en/dev/intro/reusable-apps/#packaging-your-app)

**Fixes**

- Fix PEP8 code formatting violations.
