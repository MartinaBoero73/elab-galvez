# eLab Gálvez - Payroll PDF Generator

A robust Python microservice designed to parse legacy plain-text payroll files (TXT) and generate modern, compliant, and visually polished PDF payslips (Recibos de Sueldo - Ley 20.744, Argentina). Built with FastAPI, Pydantic, and ReportLab, this service acts as a bridge between outdated enterprise software and modern, cloud-native document generation.

##  Key Features

* **Legacy Text Parsing:** Custom regex-based parsers designed to safely extract multi-line employer contributions, employee details, and complex salary items (Haberes, Deducciones, No Remunerativos) from unstructured, positional TXT exports.
* **Strict Data Validation:** Utilizes Pydantic models to ensure data integrity, automatically grouping layout sections and mathematically verifying totals before rendering.
* **High-Quality PDF Rendering:** Employs ReportLab to create pixel-perfect physical layouts featuring dynamic zebra-striping, precise column mapping, and corporate styling (dark ribbons for totals).
* **Data Visualization:** Integrates `matplotlib` to generate an embedded pie chart dynamically displaying the visual composition of the net salary versus employer costs and social security.

## Stack

* **Core:** Python 3.12+
* **API Framework:** FastAPI
* **Data Validation:** Pydantic
* **PDF Generation:** ReportLab

##  Project Structure

```text
elab-galvez/
├── src/
│   └── elab_galvez/
│       ├── api/               # FastAPI endpoints and Mangum handler
│       ├── domain/            # Pydantic models and data schemas
│       ├── parsers/           # Legacy TXT string processing and regex
│       └── services/          # PDF builder and matplotlib rendering logic
├── assets/                    # Static image files (logos, signatures)
└── README.md