# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Excel Combiner — a tool for merging/combining multiple Excel files into one. The project is in early development; update this file as the architecture takes shape.

## Git Commit Policy

**Commit frequently throughout every session** to ensure no work is lost. Specifically:
- Commit after every meaningful change (new file, new feature, bug fix, refactor)
- Commit before and after any significant structural change
- Never leave a session with uncommitted changes
- Use descriptive commit messages that explain *what* and *why*
- Always run `git status` at the end of a session to confirm everything is committed

## Update This File

Once source files exist, document here:
- How to install dependencies (e.g., `pip install -r requirements.txt`)
- How to run the tool (e.g., `python main.py`)
- Key architectural decisions (input/output format, sheet handling strategy, duplicate handling, etc.)
