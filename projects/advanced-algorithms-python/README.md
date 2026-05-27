# Advanced Algorithms Coursework Portfolio

Python implementations of four algorithm-focused coursework tasks from UFCFYR-15-2 Advanced Algorithms. The project demonstrates data processing, brute-force search with constraints, graph search, and parallel image-processing techniques.

## Project Overview

| Task | Problem | Main algorithm / technique | Entry point |
| --- | --- | --- | --- |
| 1.1 | Calculate final degree classifications from module results | Weighted aggregation with pandas DataFrames | `dataset/task1_1/DegreeCalculation.py` |
| 1.2 | Generate valid passwords from strict composition rules | Cartesian product search with rule-based filtering | `dataset/task1_2/password_generator.py` |
| 1.3 | Find cheapest or fastest rail route between stations | Dijkstra's algorithm with a priority queue | `dataset/task1_3/train_ticket_search.py` |
| 1.4 | Find matching faces in an image set | Serial and multiprocessing-based face recognition | `dataset/task1_4/task1_4_serial.py`, `dataset/task1_4/task1_4_parallel.py` |

## Repository Structure

```text
dataset/
  task1_1/  Degree classification inputs and script
  task1_2/  Password generation script
  task1_3/  Train route data and Dijkstra search script
  task1_4/  Face recognition scripts
AA REPORT.docx
README.md
requirements.txt
```

Large media files, generated CSV outputs, bundled installers, and private face image data are intentionally ignored by Git. The face-recognition task expects a `known_man.jpg` file and an `imageset/` folder inside `dataset/task1_4/` when run locally.

## Setup

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`face-recognition` depends on `dlib`, which can require extra setup on Windows. The other three tasks only need `pandas`.

## Running the Tasks

Degree classification:

```bash
python dataset/task1_1/DegreeCalculation.py
```

Password generation:

```bash
python dataset/task1_2/password_generator.py 4
```

Train route search:

```bash
python dataset/task1_3/train_ticket_search.py
```

Parallel face search:

```bash
python dataset/task1_4/task1_4_parallel.py
```

## What This Demonstrates

- Selecting data structures that match the problem, including DataFrames, sets, dictionaries, adjacency lists, heaps, and process pools.
- Applying classic algorithms such as brute-force enumeration and Dijkstra's shortest-path search.
- Improving portability by using project-relative file paths instead of machine-specific paths.
- Comparing serial and parallel approaches for CPU-heavy image-processing work.

## Notes for Recruiters

This repository is a cleaned portfolio version of a university algorithms coursework submission. The implementation emphasizes readable Python, practical algorithm selection, and clear separation between input data, processing logic, and generated outputs.
