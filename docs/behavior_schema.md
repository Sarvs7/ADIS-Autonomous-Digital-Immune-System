# ADIS Behavioral Feature Schema — V1

## 1. Purpose

Define the features used by ADIS to represent computer activity within a fixed behavioral window. The schema must be consistent across synthetic data generation, real telemetry, training and inference.

## 2. Behavioral Window

- Window duration: 60 seconds.
- Aggregation: non-overlapping windows for the initial dataset.
- Primary unit: one process per window.
- System-level events that cannot be attributed to a process must be stored separately and must not be falsely assigned to a process.
- Windows with missing telemetry must be marked as incomplete rather than treating missing values as zero.

## 3. Process Features

| Feature | Definition | Unit |
|---|---|---|
| process_snapshot_count | Number of process snapshots observed | Count |
| process_start_count | Number of process starts attributed to the process or its defined process group | Count |
| process_stop_count | Number of process stops observed | Count |
| cpu_mean | Mean CPU usage during the window | Percent |
| cpu_max | Maximum observed CPU usage | Percent |
| memory_mean | Mean memory usage during the window | Percent |
| memory_max | Maximum observed memory usage | Percent |
| thread_mean | Mean observed thread count | Count |
| thread_max | Maximum observed thread count | Count |
| child_process_count | Number of child processes created by the process | Count |
| process_age_seconds | Process age at the end of the window | Seconds |

## 4. File Features

File activity is attributed to a process only when reliable telemetry identifies the responsible process.

| Feature | Definition | Unit |
|---|---|---|
| file_create_count | File creation events attributed to the process | Count |
| file_modify_count | File modification events attributed to the process | Count |
| file_delete_count | File deletion events attributed to the process | Count |
| unique_files_touched | Number of distinct files touched during the window | Count |

## 5. Network Features

| Feature | Definition | Unit |
|---|---|---|
| network_connection_count | Newly observed connections attributed to the process | Count |
| unique_remote_ip_count | Distinct remote IP addresses contacted | Count |
| unique_remote_port_count | Distinct remote destination ports contacted | Count |

## 6. Labels

Initial controlled-dataset labels:

- BENIGN
- SUSPICIOUS

A SUSPICIOUS label means the scenario exhibits predefined suspicious behavior. It does not prove that a real file or process is malware.

Labels must be assigned from the controlled scenario definition, not guessed by the dataset-generating AI.

## 7. Data Quality Requirements

- Feature names and ordering must remain identical during training and inference.
- Missing telemetry must not silently become zero.
- Synthetic scenarios must be documented and reproducible.
- Training and evaluation splits must be separated by scenario family.
- Synthetic evaluation results must not be reported as real-world malware detection accuracy.
- No real malware execution is required to generate the initial synthetic dataset.

## 8. Safety

- DRY_RUN remains enabled.
- No automatic process termination during dataset development or model evaluation.
- The existing Isolation Forest model must be preserved for comparison.