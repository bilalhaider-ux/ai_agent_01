# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Existing React/Vite frontend with a FastAPI/Python backend.

## Users

Primary users are data analysts who upload raw datasets to profile them professionally and understand their structure, quality, distributions, and relationships.

## Product Purpose

DataSnap turns an uploaded CSV, TSV, XLSX, Parquet, JSON, or JSONL dataset into a comprehensive exploratory data analysis report. Success means the user can understand the dataset's structure and quality from trustworthy statistical summaries and data visualizations, then download the result as HTML or Markdown.

## Positioning

DataSnap provides deterministic, dataset-agnostic comprehensive EDA without invented insights. Computed facts remain separate from cleaning guidance and any future predictive-analysis work.

## Operating Context

The user uploads a dataset, optionally supplies an EDA focus, watches a staged analysis workflow, reviews a report, and may save it locally in the browser or export it as HTML or Markdown.

## Capabilities and Constraints

- Profile rows, columns, data types, missingness, duplicates, cardinality, numeric distributions, IQR outliers, skewness, kurtosis, correlations, and date/time columns.
- Generate histograms, box plots, categorical frequency charts, and numeric relationship charts.
- Keep EDA deterministic and dataset-agnostic.
- Do not silently clean or overwrite the uploaded raw dataset.
- Do not present unsupported business recommendations, causal claims, predictive accuracy, or invented insights.
- Keep cleaning guidance and future predictive analysis as separate next steps.
- Preserve the existing upload, polling, report, local storage, and download behavior.

## Brand Commitments

- Product name: DataSnap.
- Use a professional, calm, data-first voice.
- Prefer EDA, data quality, statistical summaries, distributions, relationships, visualizations, and report terminology.
- Avoid chatbot language, AI slang, decision brief language, and “visual evidence” terminology.

## Evidence on Hand

- The working EDA implementation is in `backend/app/agent/eda.py`.
- The report renderer is in `backend/app/services/report_service.py`.
- The primary frontend surfaces are in `frontend/src/App.jsx` and `frontend/src/styles.css`.
- No external testimonials, customer claims, or performance benchmarks are established; future UI must not fabricate them.

## Product Principles

1. Computed facts come from the uploaded rows.
2. Comprehensive EDA includes both non-graphical statistical summaries and data visualizations.
3. Raw data remains unchanged unless a separate, explicit cleaning workflow is introduced.
4. EDA findings, cleaning considerations, and predictive modeling remain distinct.
5. The interface should make analytical state, quality, and limitations clear.

## Accessibility & Inclusion

- Support responsive desktop, tablet, and mobile layouts.
- Respect `prefers-reduced-motion` for live analysis animations and ambient motion.
- Keep upload, progress, report, table, chart, and download actions keyboard accessible.
