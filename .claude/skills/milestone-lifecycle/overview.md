# Overview

This skill defines how to scaffold milestone-based work when a roadmap is broken into SPECs, milestones, and small implementation plans.

## Purpose

Define how large-scope work should be executed when a roadmap is broken into milestones, SPECs, and small implementation plans.

This guidance is reusable across roadmap-driven efforts. It is not specific to one feature area.

## Core Principles

- close any open decisions in the document(s) this milestone depends on before scaffolding or implementation continues
- divert to [Decision Locking](../decision-locking/SKILL.md) when required dependency documents still contain open questions
- keep milestone scope explicit
- keep task scope small enough for one agent to complete in one context window
- prefer sequential, auditable progress over large opaque implementation bursts
- require quick project scanning before implementation to avoid duplication
- require explicit handoff from earlier milestone outputs when later milestones depend on them
- require tests and verification before tasks are considered done
- require each task agent to update its own task file with status, owner, dates, and what was done before it marks the task complete
- require the coordinating agent to verify the task file's `Owner` field before handoff and, if missing, send the task back for the owner entry before completion
- make UAT as smooth as possible by catching major issues before handoff
