from faker import Faker
import csv

fake = Faker()

# Set the desired number of lines
num_lines = 500000

# Specify the fields you want in your data
fields = ['name', 'address', 'email', 'phone_number', 'date_of_birth']

# Generate synthetic data and write to a CSV file
with open('synthetic_data.csv', 'w', newline='') as csvfile:
    csvwriter = csv.DictWriter(csvfile, fieldnames=fields)

    # Write header
    csvwriter.writeheader()

    # Set to keep track of generated data
    unique_data_set = set()

    # Write synthetic data
    while len(unique_data_set) < num_lines:
        data = {
            'name': fake.name(),
            'address': fake.address(),
            'email': fake.email(),
            'phone_number': fake.phone_number(),
            'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d')
        }

        # Convert the dictionary to a frozenset to check for duplicates
        data_set = frozenset(data.items())

        # Check if data is unique before adding to the CSV and set
        if data_set not in unique_data_set:
            csvwriter.writerow(data)
            unique_data_set.add(data_set)

print(f"Synthetic data generation completed. {num_lines} unique lines written to synthetic_data.csv")
