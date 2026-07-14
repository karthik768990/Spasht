-- Tender Red-Flag Detector — schema for NeonDB (run in Neon SQL editor, in this order)

CREATE TABLE departments (
    department_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    region TEXT NOT NULL
);

CREATE TABLE vendors (
    vendor_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    registered_address TEXT,
    registration_date DATE
);

CREATE TABLE tenders (
    tender_id SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    category TEXT NOT NULL,
    region TEXT NOT NULL,
    eligibility_text TEXT NOT NULL,
    estimated_value NUMERIC(14, 2) NOT NULL,
    award_value NUMERIC(14, 2),
    published_date DATE NOT NULL,
    award_date DATE,
    status TEXT NOT NULL DEFAULT 'awarded'
);

CREATE TABLE bids (
    bid_id SERIAL PRIMARY KEY,
    tender_id INTEGER NOT NULL REFERENCES tenders(tender_id),
    vendor_id INTEGER NOT NULL REFERENCES vendors(vendor_id),
    bid_amount NUMERIC(14, 2) NOT NULL,
    is_winner BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (tender_id, vendor_id)
);

CREATE TABLE anomaly_scores (
    tender_id INTEGER PRIMARY KEY REFERENCES tenders(tender_id),
    dept_hhi NUMERIC(10, 2),
    category_hhi NUMERIC(10, 2),
    single_bidder_flag BOOLEAN,
    eligibility_deviation_score NUMERIC(6, 4),
    computed_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_tenders_department_id ON tenders(department_id);
CREATE INDEX idx_tenders_category ON tenders(category);
CREATE INDEX idx_bids_tender_id ON bids(tender_id);
CREATE INDEX idx_bids_vendor_id ON bids(vendor_id);
CREATE INDEX idx_bids_is_winner ON bids(is_winner) WHERE is_winner = TRUE;
