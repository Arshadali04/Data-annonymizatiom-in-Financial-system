import pandas as pd

K = 10
numerical_QIS = ['age']
SENSITIVE_ATTRIBUTE = 'Account_Balance'

def anonymize_with_partitioning(df, k):
    print("Preparing data for partitioning...")
    
    if SENSITIVE_ATTRIBUTE not in df.columns:
        print(f"FATAL ERROR: The sensitive attribute '{SENSITIVE_ATTRIBUTE}' was not found in the CSV file.")
        print(f"Available columns are: {list(df.columns)}")
        print("Please update the SENSITIVE_ATTRIBUTE variable if needed.")
        return None

    age_counts = df['age'].value_counts().sort_index().reset_index()
    age_counts.columns = ['age', 'count']

    partitions = []
    current_partition_ages = []
    current_partition_count = 0

    print("Creating partitions to satisfy k-anonymity...")
    for index, row in age_counts.iterrows():
        current_partition_ages.append(row['age'])
        current_partition_count += row['count']
        
        if current_partition_count >= k and len(current_partition_ages) > 1:
            partitions.append(current_partition_ages)
            current_partition_ages = []
            current_partition_count = 0

    if current_partition_ages:
        if partitions:
            print("Merging the last partition into the previous one to ensure k-anonymity and range.")
            partitions[-1].extend(current_partition_ages)
        else:
            partitions.append(current_partition_ages)
    
    print(f"Created {len(partitions)} final partitions.")

    age_to_range_map = {}
    for part in partitions:
        min_age = min(part)
        max_age = max(part)
        
        age_range_str = f"{min_age}-{max_age}"
        
        for age in part:
            age_to_range_map[age] = age_range_str

    print("Applying anonymized ranges to the dataset...")
    df_anonymized = df.copy()
    df_anonymized['age'] = df['age'].map(age_to_range_map)
    
    return df_anonymized[['age', SENSITIVE_ATTRIBUTE]]


if __name__ == "__main__":
    try:
        data = pd.read_csv("bank_details.csv", nrows=100)
        
        print("Starting data anonymization process using partitioning...")
        print(f"Target: {K}-anonymity")
        print(f"Quasi-Identifiers: {numerical_QIS}")
        print("-" * 30)

        anonymized_data = anonymize_with_partitioning(data, K)

        if anonymized_data is not None:
            output_filename = "anonymized_cluster_bank_details.csv"
            anonymized_data.to_csv(output_filename, index=False)
            
            print("-" * 30)
            print(f"Anonymization complete. Output saved to {output_filename}")
            print("Sample of anonymized data:")
            print(anonymized_data.head())

    except FileNotFoundError:
        print("Error: 'bank_details.csv' not found.")
        print("Please make sure the sample CSV file is in the same directory.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

