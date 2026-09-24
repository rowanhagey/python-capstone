# Code Review Process

## Overview
All code changes must go through peer review before merging to the main branch.

## Pull Request Requirements
Every pull request must include a description of the change, linked ticket, and test coverage notes.
Pull requests must pass all CI checks (build, lint, unit tests) before review begins.
PRs larger than 500 lines should be split into smaller, reviewable chunks where possible.

## Review Standards
At least one approval is required from a senior engineer before merging.
Reviewers check for correctness, readability, test coverage, and adherence to style guides.
Security-sensitive changes (auth, data access, encryption) require a second approval from the security team.

## Merge Policy
Squash-and-merge is the default strategy to keep history clean.
Direct pushes to main are disabled; all changes go through pull requests.
Merged branches are deleted automatically after 7 days.

## Escalation
If a reviewer and author disagree, the tech lead makes the final call.
Reviews should be completed within 2 business days of submission.

