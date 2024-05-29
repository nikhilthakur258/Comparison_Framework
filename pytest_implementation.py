import pytest
import snowflake.connector
from unittest.mock import patch, MagicMock
import pandas as pd
from io import StringIO
from SnowflakeUtilities import SnowflakeUtilities

@pytest.fixture(scope='session')
def snowflake_util():
    util = SnowflakeUtilities()
    util.open_connection(
        user='test_user',
        password='test_password',
        account='test_account',
        warehouse='test_warehouse',
        database='test_database',
        schema='test_schema'
    )
    yield util
    util.close_connection()

def test_open_connection(snowflake_util):
    assert snowflake_util.connection is not None

def test_test_connection(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        mock_cursor.return_value.fetchone.return_value = ('5.7.0',)
        result = snowflake_util.test_connection()
        assert result == ('5.7.0',)

def test_execute_query(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        snowflake_util.execute_query("CREATE TABLE test_table (id INT, name STRING)")
        mock_cursor.return_value.execute.assert_called_with("CREATE TABLE test_table (id INT, name STRING)")

def test_execute_query_and_fetch_results(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        mock_cursor.return_value.fetchall.return_value = [(1, 'Alice'), (2, 'Bob')]
        result = snowflake_util.execute_query_and_fetch_results("SELECT * FROM test_table")
        assert result == [(1, 'Alice'), (2, 'Bob')]

def test_load_data_from_csv(snowflake_util):
    with patch('pandas.read_csv') as mock_read_csv, patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        mock_read_csv.return_value = pd.read_csv(StringIO("id,name\n1,Alice\n2,Bob"))
        snowflake_util.load_data_from_csv('test_table', 'dummy_path.csv')
        expected_calls = [
            (("INSERT INTO test_table VALUES (%s, %s)", (1, 'Alice')),),
            (("INSERT INTO test_table VALUES (%s, %s)", (2, 'Bob')),)
        ]
        mock_cursor.return_value.execute.assert_has_calls(expected_calls, any_order=True)

def test_load_data_from_parquet(snowflake_util):
    with patch('pandas.read_parquet') as mock_read_parquet, patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        mock_read_parquet.return_value = pd.DataFrame({'id': [1, 2], 'name': ['Alice', 'Bob']})
        snowflake_util.load_data_from_parquet('test_table', 'dummy_path.parquet')
        expected_calls = [
            (("INSERT INTO test_table VALUES (%s, %s)", (1, 'Alice')),),
            (("INSERT INTO test_table VALUES (%s, %s)", (2, 'Bob')),)
        ]
        mock_cursor.return_value.execute.assert_has_calls(expected_calls, any_order=True)

def test_unload_data_to_csv(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor, patch('pandas.DataFrame.to_csv') as mock_to_csv:
        mock_cursor.return_value.fetchall.return_value = [(1, 'Alice'), (2, 'Bob')]
        mock_cursor.return_value.description = [('id',), ('name',)]
        snowflake_util.unload_data_to_csv("SELECT * FROM test_table", 'dummy_path.csv')
        mock_to_csv.assert_called_with('dummy_path.csv', index=False)

def test_unload_data_to_parquet(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor, patch('pandas.DataFrame.to_parquet') as mock_to_parquet:
        mock_cursor.return_value.fetchall.return_value = [(1, 'Alice'), (2, 'Bob')]
        mock_cursor.return_value.description = [('id',), ('name',)]
        snowflake_util.unload_data_to_parquet("SELECT * FROM test_table", 'dummy_path.parquet')
        mock_to_parquet.assert_called_with('dummy_path.parquet', index=False)

def test_get_table_schema(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        mock_cursor.return_value.fetchall.return_value = [('ID', 'NUMBER', None, None, None, None), ('NAME', 'STRING', None, None, None, None)]
        schema = snowflake_util.get_table_schema('test_table')
        assert schema == [('ID', 'NUMBER', None, None, None, None), ('NAME', 'STRING', None, None, None, None)]

def test_create_table(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        snowflake_util.create_table('test_table', 'id INT, name STRING')
        mock_cursor.return_value.execute.assert_called_with("CREATE TABLE test_table (id INT, name STRING)")

def test_drop_table(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        snowflake_util.drop_table('test_table')
        mock_cursor.return_value.execute.assert_called_with("DROP TABLE IF EXISTS test_table")

def test_truncate_table(snowflake_util):
    with patch.object(snowflake_util.connection, 'cursor') as mock_cursor:
        snowflake_util.truncate_table('test_table')
        mock_cursor.return_value.execute.assert_called_with("TRUNCATE TABLE test_table")


if __name__ == '__main__':
    pytest.main()
