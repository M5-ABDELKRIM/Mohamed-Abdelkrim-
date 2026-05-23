# Security Data Analytics and Visualisation

This repository presents a university security data analytics project completed in Python using Jupyter Notebooks. The work demonstrates how raw cyber-security datasets can be cleaned, explored, visualised, modelled, and interpreted to support practical security investigation.

The project is organised into three parts:

- Part 1: network packet capture analysis
- Part 2: malware family classification
- Part 3: insider-threat style behavioural investigation

## Project Overview

The aim of this project is to apply data analytics and visualisation techniques to realistic security datasets. Across the notebooks, the analysis uses packet metadata, malware feature vectors, employee activity logs, USB activity, file access records, web activity, and email communication data.

The work focuses on turning technical data into meaningful security evidence. This includes identifying unusual traffic patterns, comparing machine learning approaches for malware detection, and correlating multiple activity logs to investigate suspicious insider behaviour.

## Repository Structure

```text
Security Data Analytics and Visualisation/
+-- part1/
|   +-- 22066989-PART1.ipynb.ipynb
|   +-- packet-capture3.csv
+-- part2/
|   +-- 22066989-PART2.ipynb.ipynb
|   +-- malware_data.csv
|   +-- malware_label.csv
+-- part3/
    +-- UFCFEL-15-3-part3-22066989.ipynb
    +-- CodeCraftersInc/
    |   +-- employee_data.csv
    |   +-- login_data.csv
    |   +-- usb_data.csv
    |   +-- file_data.csv
    |   +-- web_data.csv
    |   +-- email_data.csv
    +-- exported visualisations
```

## Part 1: Packet Capture Analysis

The first notebook analyses packet capture data containing fields such as time, source, destination, protocol, packet length, and packet information.

Key work includes:

- Loading and preparing packet metadata with pandas.
- Creating time-series charts to show packet volume over time.
- Comparing protocol usage with bar charts.
- Visualising source-to-destination communication patterns.
- Building node-link diagrams with NetworkX to highlight traffic relationships.
- Creating protocol-specific boolean features.
- Interpreting findings in a security context.

The analysis identifies important traffic patterns such as high-volume internal and external communication pairs, traffic spikes, multicast/local discovery traffic, and the presence of legacy SSL protocols that would require security review.

## Part 2: Malware Classification

The second notebook works with a malware dataset containing 28,000 samples, 256 features, and malware family labels.

This section compares a simple manual classifier with larger-scale machine learning models.

Key work includes:

- Loading malware feature and label datasets.
- Building a centroid-based classifier by hand using Euclidean distance.
- Visualising reduced feature spaces and class centroids.
- Calculating prediction accuracy and confusion matrices.
- Scaling features with `StandardScaler`.
- Encoding labels with `LabelEncoder`.
- Splitting data into stratified training and test sets.
- Training and evaluating an MLP neural network classifier.
- Training and evaluating a Random Forest classifier.

Model results captured in the notebook include:

- Manual centroid classifier accuracy: 70.00%
- MLP classifier accuracy: 79.48%
- Random Forest classifier accuracy: 88.16%

This part demonstrates understanding of baseline modelling, feature scaling, supervised classification, model comparison, and the limitations of simple decision boundaries when malware families overlap.

## Part 3: Insider-Threat Investigation

The third notebook investigates activity from the CodeCraftersInc dataset. It combines employee records, login events, USB activity, file access logs, web activity, and email communication.

Key work includes:

- Loading and joining multiple behavioural datasets.
- Analysing login and logoff behaviour by job role.
- Investigating a specific workstation user pattern.
- Building email network graphs with NetworkX.
- Comparing file access activity across HR, Services, and Security roles.
- Using heatmaps and grouped metrics to compare behaviour.
- Creating anomaly indicators for off-hours logins, USB usage, and sensitive file access.
- Correlating events across time to form an evidence-based security narrative.

The investigation identifies `usr-fjl`, a Director assigned to `pc52`, as the main suspect. The notebook correlates cross-machine USB activity on Finance workstation `pc99`, sensitive HR file access, login timing, and email communication with Finance user `usr-zwh`.

The key conclusion is that the evidence suggests potential misuse of a Finance machine to copy confidential HR-related files to removable media. The notebook also notes an important limitation: the USB contents cannot be directly inspected, so the conclusion is based on correlated behavioural evidence rather than direct file-copy proof.

## Skills Demonstrated

- Python data analysis with pandas and NumPy
- Data cleaning and transformation
- Exploratory data analysis
- Security event correlation
- Network traffic analysis
- Graph analytics with NetworkX
- Data visualisation with Matplotlib and Seaborn
- Heatmaps, bar charts, scatter plots, time-series plots, and node-link diagrams
- Supervised machine learning with scikit-learn
- Manual classifier design and model benchmarking
- Security-focused interpretation and evidence-based reporting

## Technologies Used

- Python
- Jupyter Notebook
- pandas
- NumPy
- Matplotlib
- Seaborn
- NetworkX
- scikit-learn


## Why This Project Matters

This project shows the full workflow of a security analytics investigation: taking raw logs or feature data, preparing it for analysis, visualising behaviour, applying statistical and machine learning methods, and explaining the findings in a way that supports decision-making.

For hiring reviewers, this repository demonstrates practical ability in cyber-security analytics, Python-based investigation, visual storytelling, and machine learning evaluation.
