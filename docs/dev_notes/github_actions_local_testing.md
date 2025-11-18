# Local Testing of GitHub Actions with act (Arch Linux)

## What is act?
- `act` is a tool to run GitHub Actions locally using Docker.
- It helps you test workflow changes before pushing to GitHub.

## Installation (Arch Linux)
- Install with pacman:
  ```bash
  sudo pacman -Sy --noconfirm act
  ```
- Requires Docker to be installed and running.

## Basic Usage
- Run all workflows as they would on GitHub:
  ```bash
  act
  ```
- Run a specific event (e.g., push):
  ```bash
  act push
  ```
- Run a specific job:
  ```bash
  act -j <job_id>
  ```
- List available events:
  ```bash
  act -l
  ```

## Tips
- Use `-P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest` if you need a compatible runner image.
- You can pass secrets with `--secret` or use a `.secrets` file.
- Reference: https://github.com/nektos/act

---

This document is referenced in the migration plan and workflow documentation.
