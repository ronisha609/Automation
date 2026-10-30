# CodeQL Security Scanning | GitHub Actions Setup Lab

A configuration lab exploring how to connect CodeQL static analysis to a GitHub Actions workflow. This repository contains the workflow setup rather than a completed vulnerability investigation.

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

## Current Status

The repository has a configured workflow, but no application source files to scan. No workflow runs were returned when checked during this portfolio update. This project demonstrates configuration practice; it does not yet demonstrate a successful scan, findings, or remediation.

## Next Milestone

Add a small application, run the workflow, and document a real finding, its fix, and the follow-up scan. That would make this a stronger application-security case study.

[Cybersecurity labs](https://github.com/ronisha609/CyberSecurityLabs)
