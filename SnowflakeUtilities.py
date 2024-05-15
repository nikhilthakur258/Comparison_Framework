import snowflake.connector
from robot.api.deco import keyword
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import os

class SnowflakeUtilities:
    def __init__(self):
        self.connection = None

    @keyword
    def open_connection(self, user, password, account, warehouse, database, schema):
        self.connection = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema
        )

    @keyword
    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    @keyword
    def test_connection(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        result = cursor.fetchone()
        cursor.close()
        return result

    @keyword
    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        cursor.close()

    @keyword
    def execute_query_and_fetch_results(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    @keyword
    def execute_stored_procedure(self, procedure_name, *args):
        cursor = self.connection.cursor()
        cursor.callproc(procedure_name, args)
        cursor.close()

    @keyword
    def execute_query_from_file(self, file_path):
        with open(file_path, 'r') as file:
            query = file.read()
        self.execute_query(query)

    @keyword
    def load_data_from_csv(self, table_name, file_path):
        df = pd.read_csv(file_path)
        cursor = self.connection.cursor()
        for _, row in df.iterrows():
            values = tuple(row)
            placeholders = ', '.join(['%s'] * len(values))
            query = f"INSERT INTO {table_name} VALUES ({placeholders})"
            cursor.execute(query, values)
        cursor.close()

    @keyword
    def load_data_from_parquet(self, table_name, file_path):
        df = pd.read_parquet(file_path)
        cursor = self.connection.cursor()
        for _, row in df.iterrows():
            values = tuple(row)
            placeholders = ', '.join(['%s'] * len(values))
            query = f"INSERT INTO {table_name} VALUES ({placeholders})"
            cursor.execute(query, values)
        cursor.close()

    @keyword
    def unload_data_to_csv(self, query, file_path):
        cursor = self.connection.cursor()
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        df.to_csv(file_path, index=False)
        cursor.close()

    @keyword
    def unload_data_to_parquet(self, query, file_path):
        cursor = self.connection.cursor()
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        df.to_parquet(file_path, index=False)
        cursor.close()

    @keyword
    def get_table_schema(self, table_name):
        query = f"DESCRIBE TABLE {table_name}"
        cursor = self.connection.cursor()
        cursor.execute(query)
        schema = cursor.fetchall()
        cursor.close()
        return schema

    @keyword
    def create_table(self, table_name, schema):
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE TABLE {table_name} ({schema})")
        cursor.close()

    @keyword
    def drop_table(self, table_name):
        cursor = self.connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.close()

    @keyword
    def truncate_table(self, table_name):
        cursor = self.connection.cursor()
        cursor.execute(f"TRUNCATE TABLE {table_name}")
        cursor.close()

    @keyword
    def insert_data(self, table_name, *data):
        cursor = self.connection.cursor()
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table_name} VALUES ({placeholders})"
        cursor.execute(query, data)
        cursor.close()

    @keyword
    def update_data(self, table_name, set_clause, condition):
        cursor = self.connection.cursor()
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        cursor.execute(query)
        cursor.close()

    @keyword
    def delete_data(self, table_name, condition):
        cursor = self.connection.cursor()
        query = f"DELETE FROM {table_name} WHERE {condition}"
        cursor.execute(query)
        cursor.close()

    @keyword
    def create_database(self, database_name):
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE DATABASE {database_name}")
        cursor.close()

    @keyword
    def drop_database(self, database_name):
        cursor = self.connection.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
        cursor.close()

    @keyword
    def use_database(self, database_name):
        cursor = self.connection.cursor()
        cursor.execute(f"USE DATABASE {database_name}")
        cursor.close()

    @keyword
    def create_schema(self, schema_name):
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE SCHEMA {schema_name}")
        cursor.close()

    @keyword
    def drop_schema(self, schema_name):
        cursor = self.connection.cursor()
        cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name}")
        cursor.close()

    @keyword
    def use_schema(self, schema_name):
        cursor = self.connection.cursor()
        cursor.execute(f"USE SCHEMA {schema_name}")
        cursor.close()

    @keyword
    def create_user(self, user_name, password):
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE USER {user_name} PASSWORD = '{password}'")
        cursor.close()

    @keyword
    def drop_user(self, user_name):
        cursor = self.connection.cursor()
        cursor.execute(f"DROP USER IF EXISTS {user_name}")
        cursor.close()

    @keyword
    def alter_user(self, user_name, set_clause):
        cursor = self.connection.cursor()
        query = f"ALTER USER {user_name} SET {set_clause}"
        cursor.execute(query)
        cursor.close()

    @keyword
    def create_role(self, role_name):
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE ROLE {role_name}")
        cursor.close()

    @keyword
    def drop_role(self, role_name):
        cursor = self.connection.cursor()
        cursor.execute(f"DROP ROLE IF EXISTS {role_name}")
        cursor.close()

    @keyword
    def grant_role(self, role_name, to_user):
        cursor = self.connection.cursor()
        cursor.execute(f"GRANT ROLE {role_name} TO USER {to_user}")
        cursor.close()

    @keyword
    def revoke_role(self, role_name, from_user):
        cursor = self.connection.cursor()
        cursor.execute(f"REVOKE ROLE {role_name} FROM USER {from_user}")
        cursor.close()

    @keyword
    def create_warehouse(self, warehouse_name):
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE WAREHOUSE {warehouse_name}")
        cursor.close()

    @keyword
    def drop_warehouse(self, warehouse_name):
        cursor = self.connection.cursor()
        cursor.execute(f"DROP WAREHOUSE IF EXISTS {warehouse_name}")
        cursor.close()

    @keyword
    def start_warehouse(self, warehouse_name):
        cursor = self.connection.cursor()
        cursor.execute(f"ALTER WAREHOUSE {warehouse_name} RESUME")
        cursor.close()

    @keyword
    def suspend_warehouse(self, warehouse_name):
        cursor = self.connection.cursor()
        cursor.execute(f"ALTER WAREHOUSE {warehouse_name} SUSPEND")
        cursor.close()

    @keyword
    def resize_warehouse(self, warehouse_name, size):
        cursor = self.connection.cursor()
        cursor.execute(f"ALTER WAREHOUSE {warehouse_name} SET WAREHOUSE_SIZE = '{size}'")
        cursor.close()

    @keyword
    def set_session_parameter(self, parameter, value):
        cursor = self.connection.cursor()
        cursor.execute(f"ALTER SESSION SET {parameter} = {value}")
        cursor.close()

    @keyword
    def get_session_parameter(self, parameter):
        cursor = self.connection.cursor()
        cursor.execute(f"SHOW PARAMETERS LIKE '{parameter}' IN SESSION")
        result = cursor.fetchone()
        cursor.close()
        return result

    @keyword
    def list_session_parameters(self):
        cursor = self.connection.cursor()
        cursor.execute("SHOW PARAMETERS IN SESSION")
        results = cursor.fetchall()
        cursor.close()
        return results

    @keyword
    def validate_view(self, view_name, expected_results):
        query = f"SELECT * FROM {view_name}"
        cursor = self.connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results == expected_results

    @keyword
    def check_row_count(self, table_name, expected_count):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        if count == expected_count:
            return True
        else:
            return False

    @keyword
    def check_data_sanity(self, table_name):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
        data = cursor.fetchall()
        cursor.close()
        sanity_issues = []
        # Implement your data sanity checks here
        return sanity_issues

    @keyword
    def find_duplicates(self, table_name):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name} GROUP BY <primary_key_columns> HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        cursor.close()
        return duplicates

    @keyword
    def validate_business_logic(self, test_query, expected_results_query):
        cursor = self.connection.cursor()
        cursor.execute(test_query)
        test_results = cursor.fetchall()
        cursor.execute(expected_results_query)
        expected_results = cursor.fetchall()
        cursor.close()
        return test_results == expected_results

    @keyword
    def compare_datasets_and_publish_mismatch_report(self, query1, query2, report_file):
        cursor = self.connection.cursor()
        cursor.execute(query1)
        data1 = cursor.fetchall()
        cursor.execute(query2)
        data2 = cursor.fetchall()
        cursor.close()

        df1 = pd.DataFrame(data1, columns=[desc[0] for desc in cursor.description])
        df2 = pd.DataFrame(data2, columns=[desc[0] for desc in cursor.description])
        mismatches = df1.compare(df2)

        if not mismatches.empty:
            self._generate_html_report(mismatches, report_file)
            return False
        return True

    def _generate_html_report(self, mismatches, report_file):
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template('report_template.html')
        html_content = template.render(mismatches=mismatches)
        with open(report_file, 'w') as file:
            file.write(html_content)

    @keyword
    def backup_table(self, table_name, backup_file):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        df.to_csv(backup_file, index=False)
        cursor.close()

    @keyword
    def restore_table(self, table_name, backup_file):
        df = pd.read_csv(backup_file)
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE OR REPLACE TABLE {table_name} (LIKE {table_name})")
        cursor.close()
        self.load_data_from_dataframe(table_name, df)

    @keyword
    def mask_sensitive_data(self, table_name, columns_to_mask):
        cursor = self.connection.cursor()
        for column in columns_to_mask:
            cursor.execute(f"UPDATE {table_name} SET {column} = 'MASKED' WHERE {column} IS NOT NULL")
        cursor.close()

    @keyword
    def generate_test_data(self, table_name, num_rows):
        # Implement your data generation logic here (e.g., using Faker library)
        pass

    @keyword
    def purge_old_data(self, table_name, cutoff_date):
        cursor = self.connection.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE created_at < '{cutoff_date}'")
        cursor.close()

    @keyword
    def sample_data(self, table_name, sample_size):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name} SAMPLE({sample_size})")
        sampled_data = cursor.fetchall()
        cursor.close()
        return sampled_data

    @keyword
    def transform_data(self, table_name, transformation_query):
        cursor = self.connection.cursor()
        cursor.execute(f"UPDATE {table_name} SET {transformation_query}")
        cursor.close()

    @keyword
    def validate_data(self, validation_query, expected_result):
        cursor = self.connection.cursor()
        cursor.execute(validation_query)
        result = cursor.fetchall()
        cursor.close()
        if result == expected_result:
            return True
        else:
            return False

    @keyword
    def compare_schemas(self, schema1, schema2):
        cursor = self.connection.cursor()
        cursor.execute(f"SHOW TABLES IN SCHEMA {schema1}")
        tables_schema1 = set(cursor.fetchall())
        cursor.execute(f"SHOW TABLES IN SCHEMA {schema2}")
        tables_schema2 = set(cursor.fetchall())
        cursor.close()
        if tables_schema1 == tables_schema2:
            return True
        else:
            return False

    @keyword
    def encrypt_data(self, table_name, columns_to_encrypt):
        # Implement encryption logic (e.g., using cryptography library)
        pass

    @keyword
    def archive_data(self, table_name, archive_table, archive_condition):
        cursor = self.connection.cursor()
        cursor.execute(f"INSERT INTO {archive_table} SELECT * FROM {table_name} WHERE {archive_condition}")
        cursor.execute(f"DELETE FROM {table_name} WHERE {archive_condition}")
        cursor.close()

    @keyword
    def enable_audit_logging(self):
        cursor = self.connection.cursor()
        cursor.execute("ALTER ACCOUNT SET SECURITY_POLICY = 'ALL_CHANGES'")
        cursor.close()

    @keyword
    def disable_audit_logging(self):
        cursor = self.connection.cursor()
        cursor.execute("ALTER ACCOUNT UNSET SECURITY_POLICY")
        cursor.close()

    @keyword
    def refresh_materialized_view(self, view_name):
        cursor = self.connection.cursor()
        cursor.execute(f"REFRESH MATERIALIZED VIEW {view_name}")
        cursor.close()

    @keyword
    def rollback_version(self, version_id):
        # Implement version rollback logic
        pass

    @keyword
    def profile_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(f"EXPLAIN {query}")
        profile = cursor.fetchall()
        cursor.close()
        return profile
