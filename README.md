# Amity University Exam Repository

A web platform built using Django that provides Amity University students with access to previous year question papers across all 8 semesters and subjects.
Developed by: **Shikha Bhadoria** and **Sachin Prajapati**

---

## Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [How to Run Locally](#how-to-run-locally)
- [Installation &amp; Run Instructions](#installation--run-instructions)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Future Enhancement](#future-enhancement)
- [Contributing](#contributing)
- [License](#license)

---

## About the Project

This platform helps Amity students access and filter previous year question papers quickly.
It allows users to browse papers by semester, subject, and type, making exam preparation more efficient and focused.

---

## Features

- Browse question papers by semester and subject
- Upload and organize papers
- Search and filter functionality
- Simple, responsive user interface

---

## Tech Stack

- ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
- ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
- ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
- ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
- ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
- ![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
- ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
- ![PyPDF2](https://img.shields.io/badge/PyPDF2-FFD43B?style=for-the-badge&logo=python&logoColor=black)
- ![python-decouple](https://img.shields.io/badge/python--decouple-3776AB?style=for-the-badge&logo=python&logoColor=white)
- ![dj-database-url](https://img.shields.io/badge/dj--database--url-003B57?style=for-the-badge&logo=python&logoColor=white)

---

# How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/amity-exam-repo.git

   ```

---

# Installation & Run Instructions

## 1. Navigate to the project directory:

```bash
cd amity-exam-repo
```

## 2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate        # For Windows: venv\Scripts\activate
```

## 3. Install the dependencies:

```bash
pip install -r requirements.txt
```

## 4. Apply the migrations:

```bash
python manage.py migrate
```

## 5. Run the development server:

```bash
python manage.py runserver
```

## 6. Open the project in your browser

```bash
http://127.0.0.1:8000
```

---

# API Endpoints

### `/api/search/`

- **GET**: Search papers by subject code or name.

### `/api/subjects/`

- **GET**: Fetch subjects for a specific semester.

### `/api/papers/`

- **GET**: Fetch years for a specific semester.

### `/generate-report/`

- **POST**: Generate a report based on semester, year, and subject filters.

---

# Development

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (`venv`)

### Steps to Set Up Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/amity-papers-portal.git
   cd amity-papers-portal

   ```

---

# Future Enhancement

We plan to integrate a Machine Learning model to analyze the uploaded question papers and identify the most frequently repeated questions across subjects and semesters.
This feature aims to help students prioritize important topics during their exam preparation.

---

# Contributing

We welcome contributions to improve the Amity Papers Portal Project! 🎉

### How to Contribute

1. Fork the repository.
2. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature-name


   ```

---

# License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 📬 Contact

Created by [Shikha Bhadoria](https://github.com/your-github) and [Sachin Prajapati](https://github.com/your-github) – feel free to contact us!
