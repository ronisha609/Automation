# CodeQL Security Scanning | GitHub Actions Setup Lab

A configuration lab that maps CodeQL static analysis into a GitHub Actions workflow. This folder preserves a workflow configuration sample rather than a completed vulnerability investigation.

## What Is Configured

| Component | Purpose |
| --- | --- |
| Push and pull-request triggers | Request analysis when the `master` branch changes |
| Scheduled trigger | Request a weekly scan |
| Language matrix | Select JavaScript for analysis |
| Checkout step | Make the repository contents available to the job |
| CodeQL initialization | Prepare the analysis tools |
| CodeQL analysis step | Run analysis and submit results |

[View the workflow](.github/workflows/codeql.yml)

## Capabilities Demonstrated

GitHub Actions, YAML configuration, static-analysis workflow structure, scan triggers, and job permissions.

## Learning Outcomes & Practical Value

The workflow traces automated checks from repository checkout through language selection, initialization, and analysis. It also defines the permissions required to execute security scanning while separating configuration evidence from completed scan and remediation evidence.

## Current Status

The sample is stored at `codeql-github-actions/.github/workflows/codeql.yml`. GitHub Actions discovers workflows in the repository-root `.github/workflows` directory, so this nested sample does not run here. Its triggers still refer to the original `master` branch; this repository uses `main`. No new scan was run as part of this documentation review. This project documents workflow configuration; it does not claim a successful scan, findings, or remediation.

## Next Milestone

To turn this into an active case study, place an adapted workflow in the repository-root `.github/workflows` directory, align its triggers and scan scope with this repository, run it, and document actual results and any remediation. That would make this a stronger application-security case study.

[Cybersecurity labs](https://github.com/ronisha609/CyberSecurity)
