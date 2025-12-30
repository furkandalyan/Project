# CI/CD Workflow Runs Summary

This project now includes CI and CD workflows in `.github/workflows/`.

CI workflow (ci.yml):
- Trigger: push, pull_request
- Steps: checkout, setup Python 3.11, install requirements, run `python manage.py test`
- Particular runs: no runs recorded yet (run on GitHub to generate history)

CD workflow (cd.yml):
- Trigger: push to main, workflow_dispatch
- Steps: checkout, create a source archive, upload artifact
- Particular runs: no runs recorded yet (run on GitHub to generate history)
