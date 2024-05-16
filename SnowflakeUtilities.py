import snowflake.connector
from robot.api.deco import keyword
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import os

class SnowflakeUtilities:
    """
    SnowflakeUtilities provides various methods to interact with Snowflake for ETL testing and data manipulation.
    """

    def __init__(self):
        """
        Initializes the SnowflakeUtilities class.
        """
        self.connection = None

    @keyword
    def open_connection(self, user, password, account, warehouse, database, schema):
        """
        Opens a connection to Snowflake.

        :param user: The Snowflake user.
        
        :param password: The password for the Snowflake user.
        
        :param account:  Snowflake account identifier.
        
        :param warehouse:Snowflake warehouse to use.
        
        :param database:database to connect to.
        
        :param schema:schema to use.
            

         Example  :
         | Open Connection | my_user | my_password | my_account | my_warehouse | my_database | my_schema |
        """
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
        """
        Closes the connection to Snowflake.
        
        Example:
        | Close Connection |

        """
        if self.connection:
            self.connection.close()
            self.connection = None

    @keyword
    def test_connection(self):
        """
        Tests the connection to Snowflake by retrieving the current version.

        :return: The current version of the Snowflake instance.
        
        Example:
            | Test Connection |
        
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        result = cursor.fetchone()
        cursor.close()
        return result

    @keyword
    def execute_query(self, query):
        """
        Executes a given SQL query.

        :param query: The SQL query to execute.
        
        Example:   
        | Execute Query | SELECT * FROM my_table |
        
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        cursor.close()

    @keyword
    def execute_query_and_fetch_results(self, query):
        """
        Executes a given SQL query and fetches the results.

        :param query: The SQL query to execute.
        
        :return: The results of the query as a list of tuples.
        
        Example: 
        | ${results} = | Execute Query And Fetch Results | SELECT * FROM my_table |
        
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    @keyword
    def execute_stored_procedure(self, procedure_name, *args):
        """
        Executes a stored procedure with the given arguments.

        :param procedure_name: The name of the stored procedure.
        
        :param args: The arguments to pass to the stored procedure.

        Example:         
        | Execute Stored Procedure | my_procedure | arg1 | arg2 |

        """
        cursor = self.connection.cursor()
        cursor.callproc(procedure_name, args)
        cursor.close()

    @keyword
    def execute_query_from_file(self, file_path):
        """
        Executes a SQL query read from a file.

        :param file_path: The path to the file containing the SQL query.
        
        Example:
        | Execute Query From File | /path/to/query.sql |
        """
        with open(file_path, 'r') as file:
            query = file.read()
        self.execute_query(query)

    @keyword
    def load_data_from_csv(self, table_name, file_path):
        """
        Loads data from a CSV file into a specified table.

        :param table_name: The name of the table to load data into.
        
        :param file_path: The path to the CSV file.
        
        Example:
        | Load Data From CSV | my_table | /path/to/data.csv |
        """
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
        """
        Loads data from a Parquet file into a specified table.

        :param table_name: The name of the table to load data into.
        
        :param file_path: The path to the Parquet file.
        
        
         Example:
        | Load Data From Parquet | my_table | /path/to/data.parquet |
        """
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
        """
        Executes a query and unloads the results to a CSV file.

        :param query: The SQL query to execute.
        
        :param file_path: The path to the CSV file.
        
        Example:
        | Unload Data To CSV | SELECT * FROM my_table WHERE column = 'value' | /path/to/output.csv |
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        df.to_csv(file_path, index=False)
        cursor.close()

    @keyword
    def unload_data_to_parquet(self, query, file_path):
        """
        Executes a query and unloads the results to a Parquet file.

        :param query: The SQL query to execute.
        
        :param file_path: The path to the Parquet file.
        
         Example:
        | Unload Data To Parquet | SELECT * FROM my_table WHERE column = 'value' | /path/to/output.parquet |
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        df.to_parquet(file_path, index=False)
        cursor.close()

    @keyword
    def get_table_schema(self, table_name):
        """
        Retrieves the schema of a specified table.

        :param table_name: The name of the table.
        
        :return: The schema of the table as a list of tuples.
        
        Example:
        | ${schema} = | Get Table Schema | my_table |
        | Log Many | ${schema} |
        """
        query = f"DESCRIBE TABLE {table_name}"
        cursor = self.connection.cursor()
        cursor.execute(query)
        schema = cursor.fetchall()
        cursor.close()
        return schema

    @keyword
    def create_table(self, table_name, schema):
        """
        Creates a new table with the specified schema.

        :param table_name: The name of the table to create.
        
        :param schema: The schema definition for the new table.
        
        Example:
        | Create Table | my_table | id INT, name STRING, age INT |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE TABLE {table_name} ({schema})")
        cursor.close()

    @keyword
    def drop_table(self, table_name):
        """
        Drops a specified table if it exists.

        :param table_name: The name of the table to drop.
        
        Example:
        | Drop Table | my_table |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.close()

    @keyword
    def truncate_table(self, table_name):
        """
        Truncates a specified table.

        :param table_name: The name of the table to truncate.

        Example:
        | Truncate Table | my_table |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"TRUNCATE TABLE {table_name}")
        cursor.close()

    @keyword
    def insert_data(self, table_name, *data):
        """
        Inserts data into a specified table.

        :param table_name: The name of the table to insert data into.
        
        :param data: The data to insert.
        
        
         Example:
        | Insert Data | my_table | 'John', 25, 'Male' |
        """
        cursor = self.connection.cursor()
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table_name} VALUES ({placeholders})"
        cursor.execute(query, data)
        cursor.close()

    @keyword
    def update_data(self, table_name, set_clause, condition):
        """
        Updates data in a specified table based on a condition.

        :param table_name: The name of the table to update.
        
        :param set_clause: The SET clause of the update statement.
        
        :param condition: The WHERE clause of the update statement.
        
        
        Example:
        | Update Data | my_table | age = 30 | name = 'John' |
        """
        cursor = self.connection.cursor()
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        cursor.execute(query)
        cursor.close()

    @keyword
    def delete_data(self, table_name, condition):
        """
        Deletes data from a specified table based on a condition.

        :param table_name: The name of the table to delete data from.
        
        :param condition: The WHERE clause of the delete statement.
        
        Example:
        | Delete Data | my_table | age > 30 |
        """
        cursor = self.connection.cursor()
        query = f"DELETE FROM {table_name} WHERE {condition}"
        cursor.execute(query)
        cursor.close()

    @keyword
    def create_database(self, database_name):
        """
        Creates a new database.

        :param database_name: The name of the database to create.
        
        Example:
        | Create Database | my_database |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE DATABASE {database_name}")
        cursor.close()

    @keyword
    def drop_database(self, database_name):
        """
        Drops a specified database if it exists.

        :param database_name: The name of the database to drop.
        
        Example:
        | Drop Database | my_database |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
        cursor.close()

    @keyword
    def use_database(self, database_name):
        """
        Switches to a specified database.

        :param database_name: The name of the database to switch to.
        
        Example:
        | Use Database | my_database |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"USE DATABASE {database_name}")
        cursor.close()

    @keyword
    def create_schema(self, schema_name):
        """
        Creates a new schema.

        :param schema_name: The name of the schema to create.
        
        Example:
        | Create Schema | my_schema |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE SCHEMA {schema_name}")
        cursor.close()

    @keyword
    def drop_schema(self, schema_name):
        """
        Drops a specified schema if it exists.

        :param schema_name: The name of the schema to drop.
        
        Example:
        | Drop Schema | my_schema |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name}")
        cursor.close()

    @keyword
    def use_schema(self, schema_name):
        """
        Switches to a specified schema.

        :param schema_name: The name of the schema to switch to.
        
        Example:
        | Use Schema | my_schema |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"USE SCHEMA {schema_name}")
        cursor.close()

    @keyword
    def get_query_result_with_jinja(self, query_template_file, variables, template_dir='templates'):
        """
        Renders a SQL query from a Jinja template and executes it.

        :param query_template_file: The Jinja template file for the query.
        
        :param variables: The variables to use in the Jinja template.
        
        :param template_dir: The directory where the Jinja templates are stored.
        
        :return: The result of the executed query.
        
        Example:         
        | Get Query Result With Jinja | my_query_template.sql | ${my_variables} | my_template_directory |
        """
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(query_template_file)
        query = template.render(variables)
        return self.execute_query_and_fetch_results(query)

    @keyword
    def create_user(self, user_name, password):
        """
        Creates a new user in Snowflake.

        :param user_name: The name of the user to create.
        
        :param password: The password for the new user.
        
        Example:         
        | Create User | my_user | my_password |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE USER {user_name} PASSWORD = '{password}'")
        cursor.close()

    @keyword
    def drop_user(self, user_name):
        """
        Drops a specified user if they exist.

        :param user_name: The name of the user to drop.
        
        Example:        
        | Drop User | my_user |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"DROP USER IF EXISTS {user_name}")
        cursor.close()

    @keyword
    def alter_user(self, user_name, set_clause):
        """
        Alters a specified user based on a set clause.

        :param user_name: The name of the user to alter.
        
        :param set_clause: The SET clause for altering the user.
        
         Example:       
        | Alter User | my_user | SET PASSWORD_EXPIRY_TIME = '90' |

        """
        cursor = self.connection.cursor()
        query = f"ALTER USER {user_name} SET {set_clause}"
        cursor.execute(query)
        cursor.close()

    @keyword
    def create_role(self, role_name):
        """
        Creates a new role in Snowflake.

        :param role_name: The name of the role to create.
        
        Example:         
        | Create Role | my_role |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE ROLE {role_name}")
        cursor.close()

    @keyword
    def drop_role(self, role_name):
        """
        Drops a specified role if it exists.

        :param role_name: The name of the role to drop.
        
        Example:          
        | Drop Role | my_role |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"DROP ROLE IF EXISTS {role_name}")
        cursor.close()

    @keyword
    def grant_role(self, role_name, to_user):
        """
        Grants a role to a specified user.

        :param role_name: The name of the role to grant.
        
        :param to_user: The user to grant the role to.
        
        Example:        
        | Grant Role | my_role | TO USER my_user |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"GRANT ROLE {role_name} TO USER {to_user}")
        cursor.close()

    @keyword
    def revoke_role(self, role_name, from_user):
        """
        Revokes a role from a specified user.

        :param role_name: The name of the role to revoke.
        
        :param from_user: The user to revoke the role from.
        
        Example: 
        | Revoke Role | my_role | FROM USER my_user |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"REVOKE ROLE {role_name} FROM USER {from_user}")
        cursor.close()

    @keyword
    def create_warehouse(self, warehouse_name):
        """
        Creates a new warehouse in Snowflake.

        :param warehouse_name: The name of the warehouse to create.
        
        Example:
        | Create Warehouse | my_warehouse |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE WAREHOUSE {warehouse_name}")
        cursor.close()

    @keyword
    def drop_warehouse(self, warehouse_name):
        """
        Drops a specified warehouse if it exists.

        :param warehouse_name: The name of the warehouse to drop.
        
        
          Example:         
        | Drop Warehouse | my_warehouse |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"DROP WAREHOUSE IF EXISTS {warehouse_name}")
        cursor.close()

    @keyword
    def start_warehouse(self, warehouse_name):
        """
        Resumes a specified warehouse.

        :param warehouse_name: The name of the warehouse to resume.
        
          Example:   
        | Start Warehouse | my_warehouse |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"ALTER WAREHOUSE {warehouse_name} RESUME")
        cursor.close()

    @keyword
    def suspend_warehouse(self, warehouse_name):
        """
        Suspends a specified warehouse.

        :param warehouse_name: The name of the warehouse to suspend.
        
          Example:          
        | Suspend Warehouse | my_warehouse |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"ALTER WAREHOUSE {warehouse_name} SUSPEND")
        cursor.close()

    @keyword
    def resize_warehouse(self, warehouse_name, size):
        """
        Resizes a specified warehouse.

        :param warehouse_name: The name of the warehouse to resize.
        
        :param size: The new size for the warehouse.
        
          Example:        
        | Resize Warehouse | my_warehouse | SMALL |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"ALTER WAREHOUSE {warehouse_name} SET WAREHOUSE_SIZE = '{size}'")
        cursor.close()

    @keyword
    def set_session_parameter(self, parameter, value):
        """
        Sets a session parameter in Snowflake.

        :param parameter: The parameter to set.
        
        :param value: The value to set for the parameter.
        
          Example:       
        | Set Session Parameter | TIMEZONE = 'America/New_York' |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"ALTER SESSION SET {parameter} = {value}")
        cursor.close()

    @keyword
    def get_session_parameter(self, parameter):
        """
        Retrieves the value of a session parameter in Snowflake.

        :param parameter: The parameter to retrieve.
        
        :return: The value of the session parameter.

         Example:        
        | ${timezone} = | Get Session Parameter | TIMEZONE |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"SHOW PARAMETERS LIKE '{parameter}' IN SESSION")
        result = cursor.fetchone()
        cursor.close()
        return result

    @keyword
    def list_session_parameters(self):
        """
        Lists all session parameters in Snowflake.

        :return: A list of all session parameters.
        
         Example:         
        | ${parameters} = | List Session Parameters |

        """
        cursor = self.connection.cursor()
        cursor.execute("SHOW PARAMETERS IN SESSION")
        results = cursor.fetchall()
        cursor.close()
        return results

    @keyword
    def validate_view(self, view_name, expected_results):
        """
        Validates a view by comparing its results to expected results.

        :param view_name: The name of the view to validate.
        
        :param expected_results: The expected results to compare against.
        
        :return: True if the results match, False otherwise.
        
         Example:         
        | ${is_valid} = | Validate View | my_view | ${expected_results} |

        """
        query = f"SELECT * FROM {view_name}"
        cursor = self.connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results == expected_results

    @keyword
    def check_row_count(self, table_name, expected_count):
        """
        Checks the row count of a specified table.

        :param table_name: The name of the table to check.
        
        :param expected_count: The expected row count.
        
        :return: True if the row count matches, False otherwise.
        
         Example:        
        | ${is_valid} = | Check Row Count | my_table | 100 |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        return count == expected_count

    @keyword
    def check_data_sanity(self, table_name):
        """
        Performs sanity checks on data in a specified table.

        :param table_name: The name of the table to check.
        
        :return: A list of sanity issues found.
        """
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
        data = cursor.fetchall()
        cursor.close()
        sanity_issues = []
        # Implement your data sanity checks here
        return sanity_issues

    @keyword
    def find_duplicates(self, table_name, primary_key_columns):
        """
        Finds duplicate rows in a specified table based on primary key columns.

        :param table_name: The name of the table to check.
        
        :param primary_key_columns: List of primary key column names.
        
        :return: A list of duplicate rows.

        Example:
        | ${duplicates} = | Find Duplicates | my_table | ['column1', 'column2'] |
        """
        # Concatenate primary key column names into a comma-separated string
        column_names = ', '.join(primary_key_columns)
        
        # Execute SQL query to find duplicates
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name} GROUP BY {column_names} HAVING COUNT(*) > 1")
        
        # Fetch duplicate rows
        duplicates = cursor.fetchall()
        cursor.close()
        return duplicates


    @keyword
    def validate_business_logic(self, test_query, expected_results_query):
        """
        Validates business logic by comparing the results of two queries.

        :param test_query: The query to test.
        
        :param expected_results_query: The query with the expected results.
        
        :return: True if the results match, False otherwise.
        
        Example:         
        | ${is_valid} = | Validate Business Logic | ${test_query} | ${expected_results_query} |

        """
        cursor = self.connection.cursor()
        cursor.execute(test_query)
        test_results = cursor.fetchall()
        cursor.execute(expected_results_query)
        expected_results = cursor.fetchall()
        cursor.close()
        return test_results == expected_results

    @keyword
    def compare_datasets_and_publish_mismatch_report(self, query1, query2, report_file):
        """
        Compares two datasets and publishes a mismatch report.

        :param query1: The first query to execute.
        
        :param query2: The second query to execute.
        
        :param report_file: The file to publish the mismatch report to.
        
        :return: True if there are no mismatches, False otherwise.

        Example:          
        | ${result} = | Compare Datasets And Publish Mismatch Report | ${query1} | ${query2} | ${report_file} |

        """
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
        """
        Generates an HTML report for mismatches.

        :param mismatches: The mismatches to include in the report.
        
        :param report_file: The file to save the report to.
        """
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template('report_template.html')
        html_content = template.render(mismatches=mismatches)
        with open(report_file, 'w') as file:
            file.write(html_content)

    @keyword
    def backup_table(self, table_name, backup_file):
        """
        Backs up a specified table to a file.

        :param table_name: The name of the table to back up.
        
        :param backup_file: The file to save the backup to.
        
        Example:         
        | Backup Table | my_table | my_backup.csv |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        df.to_csv(backup_file, index=False)
        cursor.close()

    @keyword
    def restore_table(self, table_name, backup_file):
        """
        Restores a table from a backup file.

        :param table_name: The name of the table to restore.
        
        :param backup_file: The file to restore the table from.
        
        
        Example:          
        | Restore Table | my_table | my_backup.csv |

        """
        df = pd.read_csv(backup_file)
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE OR REPLACE TABLE {table_name} (LIKE {table_name})")
        cursor.close()
        self.load_data_from_dataframe(table_name, df)

    @keyword
    def mask_sensitive_data(self, table_name, columns_to_mask):
        """
        Masks sensitive data in specified columns of a table.

        :param table_name: The name of the table containing the data to mask.
        
        :param columns_to_mask: The columns to mask.

        Example:       
        | Mask Sensitive Data | my_table | [ 'column1', 'column2' ] |

        """
        cursor = self.connection.cursor()
        for column in columns_to_mask:
            cursor.execute(f"UPDATE {table_name} SET {column} = 'MASKED' WHERE {column} IS NOT NULL")
        cursor.close()

    @keyword
    def generate_test_data(self, table_name, num_rows):
        """
        Generates test data for a specified table.

        :param table_name: The name of the table to generate test data for.
        
        :param num_rows: The number of rows of test data to generate.

        Example:
        | Generate Test Data | my_table | 100 |
        """
        fake = Faker()
        columns = ["col1", "col2", "col3"]  # Define your column names
        data = []

        for _ in range(num_rows):
            row = [fake.name(), fake.email(), fake.date_of_birth()]  # Sample data
            data.append(row)

        df = pd.DataFrame(data, columns=columns)
        self.load_data_from_dataframe(table_name, df)
        
        
    @keyword
    def purge_old_data(self, table_name, cutoff_date):
        """
        Purges old data from a specified table based on a cutoff date.

        :param table_name: The name of the table to purge data from.
        
        :param cutoff_date: The cutoff date for purging data.
        
        Example:         
        | Purge Old Data | my_table | '2022-01-01' |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE created_at < '{cutoff_date}'")
        cursor.close()

    @keyword
    def sample_data(self, table_name, sample_size):
        """
        Samples data from a specified table.

        :param table_name: The name of the table to sample data from.
        
        :param sample_size: The size of the sample.
        
        :return: The sampled data.

        Example:         
        | ${sampled_data} = | Sample Data | my_table | 10 |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name} SAMPLE({sample_size})")
        sampled_data = cursor.fetchall()
        cursor.close()
        return sampled_data

    @keyword
    def transform_data(self, table_name, transformation_query):
        """
        Transforms data in a specified table based on a query.

        :param table_name: The name of the table to transform data in.
        
        :param transformation_query: The query to use for the transformation.
        
        Example:          
        | Transform Data | my_table | 'column1 = column1 * 2' |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"UPDATE {table_name} SET {transformation_query}")
        cursor.close()

    @keyword
    def validate_data(self, validation_query, expected_result):
        """
        Validates data based on a query and expected result.

        :param validation_query: The query to validate data with.
        
        :param expected_result: The expected result to compare against.
        
        :return: True if the result matches the expected result, False otherwise.
        
        Example:         
        | ${is_valid} = | Validate Data | ${validation_query} | ${expected_result} |

        """
        cursor = self.connection.cursor()
        cursor.execute(validation_query)
        result = cursor.fetchall()
        cursor.close()
        return result == expected_result

    @keyword
    def compare_schemas(self, schema1, schema2):
        """
        Compares two schemas to see if they are identical.

        :param schema1: The first schema to compare.
        
        :param schema2: The second schema to compare.
        
        :return: True if the schemas are identical, False otherwise.
        
        
        Example: 
        | ${are_equal} = | Compare Schemas | schema1 | schema2 |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"SHOW TABLES IN SCHEMA {schema1}")
        tables_schema1 = set(cursor.fetchall())
        cursor.execute(f"SHOW TABLES IN SCHEMA {schema2}")
        tables_schema2 = set(cursor.fetchall())
        cursor.close()
        return tables_schema1 == tables_schema2

    @keyword
    def encrypt_data(self, table_name, columns_to_encrypt):
        """
        Encrypts data in specified columns of a table.

        :param table_name: The name of the table containing the data to encrypt.
        
        :param columns_to_encrypt: The columns to encrypt.
        
        Example:         
        | Encrypt Data | my_table | [ 'column1', 'column2' ] |

        """
        # Implement encryption logic (e.g., using cryptography library)
        pass

    @keyword
    def archive_data(self, table_name, archive_table, archive_condition):
        """
        Archives data from a specified table to an archive table based on a condition.

        :param table_name: The name of the table to archive data from.
        
        :param archive_table: The name of the archive table.
        
        :param archive_condition: The condition to use for archiving data.
        
        Example:         
        | Archive Data | my_table | archive_table | archive_condition |
        """
        cursor = self.connection.cursor()
        cursor.execute(f"INSERT INTO {archive_table} SELECT * FROM {table_name} WHERE {archive_condition}")
        cursor.execute(f"DELETE FROM {table_name} WHERE {archive_condition}")
        cursor.close()

    @keyword
    def enable_audit_logging(self):
        """
        Enables audit logging in Snowflake.
        
        Example:          
        | Enable Audit Logging |
        """
        cursor = self.connection.cursor()
        cursor.execute("ALTER ACCOUNT SET SECURITY_POLICY = 'ALL_CHANGES'")
        cursor.close()

    @keyword
    def disable_audit_logging(self):
        """
        Disables audit logging in Snowflake.

        Example:        
        | Disable Audit Logging |
        """
        cursor = self.connection.cursor()
        cursor.execute("ALTER ACCOUNT UNSET SECURITY_POLICY")
        cursor.close()

    @keyword
    def refresh_materialized_view(self, view_name):
        """
        Refreshes a materialized view.

        :param view_name: The name of the materialized view to refresh.
        
        Example:
        | Refresh Materialized View | my_view |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"REFRESH MATERIALIZED VIEW {view_name}")
        cursor.close()

    @keyword
    def profile_query(self, query):
        """
        Profiles a query to see its execution plan.

        :param query: The query to profile.
        
        :return: The execution plan of the query.
        
        Example:         
        | ${profile} = | Profile Query | SELECT * FROM my_table |

        """
        cursor = self.connection.cursor()
        cursor.execute(f"EXPLAIN {query}")
        profile = cursor.fetchall()
        cursor.close()
        return profile

    @keyword
    def compare_table_data(self, table_name_1, table_name_2):
        """
        Compares data between two tables.

        :param table_name_1: The first table to compare.
        
        :param table_name_2: The second table to compare.
        
        :return: A DataFrame of mismatches or a message if no mismatches are found.

        Example:          
        | ${mismatches} = | Compare Table Data | table1 | table2 |

        """
        cursor = self.connection.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name_1}")
        data1 = cursor.fetchall()
        columns1 = [desc[0] for desc in cursor.description]
        
        cursor.execute(f"SELECT * FROM {table_name_2}")
        data2 = cursor.fetchall()
        columns2 = [desc[0] for desc in cursor.description]
        
        cursor.close()
        
        df1 = pd.DataFrame(data1, columns=columns1)
        df2 = pd.DataFrame(data2, columns=columns2)
        
        mismatches = df1.compare(df2)
        
        if not mismatches.empty:
            return mismatches
        else:
            return "No mismatches found"

    @keyword
    def export_table_data(self, table_name, file_path, file_format):
        """
        Exports data from a table to a file in the specified format.

        :param table_name: The name of the table to export data from.
        
        :param file_path: The file path to save the exported data.
        
        :param file_format: The format to export the data in ('csv' or 'parquet').
        
        :return: A message indicating successful export.
        
        Example:    
        | Export Table Data | my_table | my_data.csv | csv |

        """
        cursor = self.connection.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        cursor.close()
        
        df = pd.DataFrame(data, columns=columns)
        
        if file_format.lower() == 'csv':
            df.to_csv(file_path, index=False)
        elif file_format.lower() == 'parquet':
            df.to_parquet(file_path, index=False)
        else:
            return "Unsupported file format. Please use 'csv' or 'parquet'."
        
        return f"Data successfully exported to {file_path}"


@keyword
def import_table_data(self, file_path, table_name, file_format):
    """
    Imports data from a file into a specified table.

    :param file_path: The path to the file containing the data to import.
    
    :param table_name: The name of the table to import data into.
    
    :param file_format: The format of the file ('csv' or 'parquet').
    
    :return: A message indicating successful import.
    
    :raises ValueError: If the file format is not supported.
    
    Example:
    | Import Table Data | my_data.csv | my_table | csv |

    """
    if file_format.lower() == 'csv':
        df = pd.read_csv(file_path)
    elif file_format.lower() == 'parquet':
        df = pd.read_parquet(file_path)
    else:
        raise ValueError("Unsupported file format. Please use 'csv' or 'parquet'.")

    cursor = self.connection.cursor()
    
    for _, row in df.iterrows():
        values = tuple(row)
        placeholders = ', '.join(['%s'] * len(values))
        query = f"INSERT INTO {table_name} VALUES ({placeholders})"
        cursor.execute(query, values)
    
    cursor.close()
    return f"Data imported into {table_name} successfully"
