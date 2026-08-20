# DemandPulse Data Card

## Dataset Overview

The DemandPulse platform operates on the benchmark e-commerce retail dataset **`FreshRetailNet-50K`**, published by Dingdong Inc. and hosted on Hugging Face.

| Attribute | Specification |
| :--- | :--- |
| **Dataset Name** | `Dingdong-Inc/FreshRetailNet-50K` |
| **Source Platform** | Hugging Face Datasets (`datasets.load_dataset(..., streaming=True)`) |
| **Primary Domain** | Fresh grocery & e-commerce retail demand planning |
| **Time Granularity** | Daily aggregated records per store-product pair |
| **Hierarchy Levels** | 5 levels: `Company → City → Store → Store-Category → Product` |

---

## Dataset Schema

| Field Name | Data Type | Field Role | Description |
| :--- | :--- | :--- | :--- |
| `date` | `string` / `datetime64` | Time Key | Calendar date of observation (`YYYY-MM-DD`). |
| `store_id` | `string` / `categorical` | Hierarchy Key | Unique identifier for retail store location. |
| `product_id` | `string` / `categorical` | Hierarchy Key | Unique SKU / product identifier. |
| `city` | `string` / `categorical` | Hierarchy Key | City location of store. |
| `category_id` | `string` / `categorical` | Hierarchy Key | Product category identifier. |
| `sale_amount` | `float64` | **Target Variable** | Normalized daily unit sales demand. |
| `promotion` | `int64` | **Treatment Variable** | Binary indicator ($1 =$ active promotion/discount, $0 =$ regular price). |
| `price` | `float64` | Feature | Item listing price. |
| `discount` | `float64` | Feature | Percentage discount applied. |
| `stock_status` | `int64` | Feature | Binary indicator ($1 =$ in stock during day, $0 =$ out of stock). |

---

## Sampling & Materialization Methodology

To enable reproducible development without local dataset downloads, DemandPulse uses streaming materialization:

- **Deterministic Hash Selection**: Series are selected using SHA-256 hashing of `(store_id, product_id)` modulo 100 against a configurable `SERIES_SAMPLE_PERCENT` threshold (default: 30%).
- **Series Integrity**: Filtering occurs at the **complete series level** rather than random row sampling, ensuring zero temporal gaps or broken lag histories.
- **Batch Materialization**: Processed in memory-efficient 50,000-row streaming batches.

---

## Known Data Limitations

### 1. Stockout Censoring
Observed `sale_amount` represents **realized sales** rather than true unconstrained customer demand. On days where `stock_status = 0`, demand is right-censored at available stock levels. DemandPulse flags out-of-stock periods during feature engineering.

### 2. Target Normalization
`sale_amount` values are pre-normalized by the dataset providers for commercial privacy. Consequently, absolute inventory recommendations reflect normalized index units rather than raw physical crate counts.

### 3. Sparse / Intermittent Demand
A subset of products in long-tail categories exhibit intermittent sales patterns with high zero counts ($>60\%$ zero days).

---

## Privacy & Ethical Considerations

- **Anonymization**: All store IDs, product IDs, customer identities, and pricing amounts are fully anonymized.
- **No PII**: The dataset contains zero Personally Identifiable Information (PII) or user tracking identifiers.
- **Commercial Usage**: Licensed under open scientific research terms via Hugging Face.
