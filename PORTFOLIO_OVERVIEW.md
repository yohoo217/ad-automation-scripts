# Ad Workflow Automation Dashboard - Portfolio Overview

## Project Summary

This project demonstrates how to refactor high-repetition, cross-system, error-prone manual workflows into a visualization-rich web platform with reusable browser automation. The Ad Workflow Automation Dashboard transforms manual advertising operations into a scalable, repeatable system.

## Technical Highlights

**Architecture & Modularity**
- Built as a full Flask web application rather than standalone scripts
- Organized by responsibility with clear separation of routes, templates, services, and utilities
- Reusable components across multiple workflow variants

**Multi-Format Content Handling**
- Different content formats implemented through shared Jinja2 templates
- Consistent field structures across single-item and batch processing flows
- Flexible routing system for variant workflows

**Automation & Integration**
- Playwright-powered browser automation handles complex form submission and multi-step task execution
- Batch processing capabilities with file upload, validation, and error reporting
- Integrated reporting and screenshot generation with database lookups

**Production-Ready Design**
- Comprehensive error handling and logging throughout the application
- Secure credential management through environment variables (no hardcoded secrets)
- Data sanitization for safe public sharing while preserving engineering patterns

## Portfolio Presentation Strategy

**When Discussing the Project:**

1. Start with the dashboard overview - explain this is a "workflow platform" not a one-off script
2. Show single-item creation flows and batch processing pages - demonstrate how the same field structures serve multiple workflow types
3. Walk through Playwright automation - show how form data is submitted to external platforms
4. Highlight the reporting and screenshot modules - demonstrate data integration and post-processing capabilities
5. Conclude with: "The public version removes sensitive information while preserving the engineering approach and implementation patterns"

**Key Points to Emphasize**

- This is workflow automation, not just UI automation
- A repeatable system productized from manual operations
- Proper security boundaries for public sharing without exposing operational details

**What Not to Discuss**

- Real organization names or URLs
- Production credentials or service accounts
- Business-logic-revealing field names
- Specific client information or proprietary processes
