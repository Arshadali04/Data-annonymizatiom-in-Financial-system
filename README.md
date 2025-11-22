Here is the **README in plain text format** exactly as you asked — no markdown formatting, no special characters, just clean text you can paste anywhere:

---

DATA ANONYMIZATION IN FINANCIAL SYSTEMS
A Mini Project on Privacy-Preserving Data Transformation

PROJECT OVERVIEW
This project focuses on anonymizing sensitive financial customer data using multiple privacy techniques. The goal is to protect identifiable information while keeping the dataset useful for analysis. The script applies methods such as k-anonymity, masking, pseudonymization, generalization, and tokenization.

DATASET
The input dataset is a CSV file named:
bankdetails.csv

It contains columns like:
Name, Age, City, Bank, Account Number, Aadhaar Number, UPI ID, IFSC, Balance, Gender, Phone, Email.

FEATURES IMPLEMENTED

1. K-ANONYMITY (K = 10)
   Age values are grouped into broad ranges such as 30-35, 40-45, etc.
   This ensures no single person can be uniquely identified by age.

2. BALANCE GENERALIZATION
   Balance amounts are grouped into 10,000-rupee ranges.
   Examples:
   32415 becomes 30000-40000
   50220 becomes 50000-60000

3. PHONE NUMBER MASKING
   Only the last 4 digits of the phone are visible.
   Example: ********3210

4. EMAIL TOKENIZATION
   Emails are replaced with unique irreversible tokens.
   Example:
   [john.doe@gmail.com](mailto:john.doe@gmail.com) becomes email_000001

5. PSEUDONYMIZATION (SHA-256 BASED)
   Used for Aadhaar, Account Number, and UPI user part.
   These values are replaced with irreversible numeric strings.

6. IFSC MASKING
   The first 4 characters are kept, the rest are masked.
   Example: HDFC0001234 becomes HDFC*******

7. FAKE NAME GENERATION
   Real names are replaced with synthetic names generated using the Faker library.

8. CITY TO REGION GENERALIZATION
   City names are converted into hashed region clusters.
   Example: Bengaluru becomes Region_3
   This hides exact location and reduces re-identification risks.

TECHNOLOGIES USED
Python
Pandas
Hashlib
Faker

HOW TO RUN THE SCRIPT

1. Install dependencies:
   pip install pandas faker

2. Run the script:
   python anonymize.py

3. Output file generated:
   anonymized_bankdetails.csv

PROJECT STRUCTURE
bankdetails.csv                        Input dataset
anonymize.py                           Main anonymization script
anonymized_bankdetails.csv             Output dataset
README.txt                             Documentation

PRIVACY GOALS ACHIEVED
k-Anonymity for identity protection
Generalization to reduce detail
Masking to hide partial sensitive data
Pseudonymization to protect numeric identifiers
Tokenization to hide emails
Fake names for full identity protection

FUTURE ENHANCEMENTS
Add l-diversity
Add t-closeness
Automatic city to state mapping using external database
Configurable privacy levels
GUI tool for anonymization

AUTHOR
Arshad Athani
Computer Science Engineering Student
Focused on Data Privacy and Cybersecurity
