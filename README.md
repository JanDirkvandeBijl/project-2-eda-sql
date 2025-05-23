# Delivery Insights Dashboard

## Overview

**Delivery Insights Dashboard** is a modular data analytics application focused on the procurement process and supplier performance. It transforms raw JSON datasets from internal APIs into insightful, interactive visualizations. The tool is intended to help supply chain analysts, procurement teams, and operational managers understand where deliveries deviate from planning and identify improvement opportunities.

The application is built using:

- **Python** for backend data transformation and analytics
- **Pandas & NumPy** for data manipulation
- **Streamlit** for the interactive frontend UI
- **Plotly** for visually rich, customizable charts
- **Scipy** for statistical testing and significance analysis

All data transformations and visual outputs are dynamically generated based on user input, allowing deep dive exploration without needing to code.

---

## Features

### ✅ Automated Data Ingestion
- Downloads and caches procurement and delivery datasets from local JSON endpoints
- Ensures repeatable and fail-safe fetching using fallback and logging logic

### 🧼 Robust Data Cleaning
- Utilizes a reusable `DataFrameCleaner` utility to standardize column types and formats
- Handles datetime conversion, missing values, string normalization, and invalid data filtering

### 📦 Delivery Performance Tracking
- Calculates **expected vs. actual delivery dates** per order line
- Derives key indicators such as:
  - Whether a line was **fully delivered**
  - Number of deliveries per order line
  - Delay in days (positive or negative) relative to expected delivery

### 📊 Advanced Visualizations
- Uses **Plotly** for bar, line, and stacked visualizations
- Includes supplier filtering, top-X percent segmentation, and missing value detection
- Shows both **order-level** and **order-line-level** analyses

### 📈 Timeliness & Trends
- Tracks monthly delivery frequency per supplier
- Visualizes how suppliers perform over time
- Automatically highlights most active suppliers

### 📉 Statistical Insights
- Performs chi-squared tests for independence between delivery categories and responsible staff
- Calculates **Cramér’s V** to evaluate effect strength
- Flags statistically significant results and displays contingency tables interactively

### 🧭 Interactive Filtering
- Year selector: isolate one or multiple years of delivery data
- Supplier selector: choose specific suppliers or rely on automatic relevance filtering (top %)
- Modular layout in Streamlit tabs for clarity and drilldown

---

## Project Structure

