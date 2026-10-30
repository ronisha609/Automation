# CodeQL Security Scanning | GitHub Actions Setup Lab

A configuration lab exploring how to connect CodeQL static analysis to a GitHub Actions workflow. This folder preserves a workflow configuration sample rather than a completed vulnerability investigation.

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

## Skills This Project Covers

GitHub Actions, YAML configuration, static-analysis workflow structure, scan triggers, and job permissions.

## Learning Outcomes & Practical Value

This lab helps explain how automated checks are triggered, how a workflow selects a language, and why permissions matter. Learners can trace the YAML from checkout through analysis. Hiring teams can review configuration knowledge while recognizing that successful execution and remediation are separate milestones.

## Current Status

The sample is stored at `codeql-github-actions/.github/workflows/codeql.yml`. GitHub Actions discovers workflows in the repository-root `.github/workflows` directory, so this nested sample does not run here. Its triggers still refer to the original `master` branch; this repository uses `main`. No new scan was run as part of this documentation review. This project demonstrates configuration practice, without evidence here of a successful scan, findings, or remediation.

## Next Milestone

To turn this into an active case study, place an adapted workflow in the repository-root `.github/workflows` directory, align its triggers and scan scope with this repository, run it, and document actual results and any remediation. That would make this a stronger application-security case study.

[Cybersecurity labs](https://github.com/ronisha609/CyberSecurity)
