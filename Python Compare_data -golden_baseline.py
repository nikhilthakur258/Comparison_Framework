import pandas as pd
import argparse
import os

def compare_csv(file1, file2, output_file, key_cols=None, report_type="full", compare_cols=None):
    chunk_size = 100000  # Adjust based on available memory and performance
    same_count = 0
    diff_count = 0
    total_count = 0

    # Open the output HTML file in write mode
    with open(output_file, 'w') as f:
        # Write the initial part of the HTML file
        f.write('''
        <html>
        <head>
        <style>
            td {padding: 5px;} 
            .diff {background-color: red;} 
            .same {background-color: white;} 
            .match {background-color: green;}
            table {border-collapse: collapse;}
            th, td {border: 1px solid black;}
        </style>
        </head>
        <body>
        ''')

        # Write the summary placeholder
        f.write('<h2>Comparison Summary</h2>')
        f.write('<p>File 1: {}</p>'.format(file1))
        f.write('<p>File 2: {}</p>'.format(file2))
        f.write('<p id="summary"></p>')

        f.write('<table id="comparisonTable">')

        # Process files in chunks
        chunk_iter1 = pd.read_csv(file1, chunksize=chunk_size, dtype=str, keep_default_na=False)
        chunk_iter2 = pd.read_csv(file2, chunksize=chunk_size, dtype=str, keep_default_na=False)

        # Write the table headers
        headers_written = False

        for chunk1, chunk2 in zip(chunk_iter1, chunk_iter2):
            if list(chunk1.columns) != list(chunk2.columns):
                raise ValueError("CSV files have different columns")

            # Determine columns to compare
            if compare_cols:
                all_columns = compare_cols
            else:
                all_columns = chunk1.columns

            if key_cols:
                chunk1.set_index(key_cols, inplace=True)
                chunk2.set_index(key_cols, inplace=True)
                chunk1.reset_index(inplace=True)
                chunk2.reset_index(inplace=True)

            diff_chunk = pd.DataFrame()
            for col in all_columns:
                diff_chunk[col + '_file1'] = chunk1[col].astype(str)
                diff_chunk[col + '_file2'] = chunk2[col].astype(str)
                diff_chunk[col + '_diff'] = chunk1.apply(
                    lambda row, col=col: 'Same' if row[col] == chunk2.at[row.name, col] else 'Different',
                    axis=1
                )

            same_rows = diff_chunk.apply(lambda row: all(row[col + '_diff'] == 'Same' for col in all_columns), axis=1)
            diff_rows = diff_chunk.apply(lambda row: any(row[col + '_diff'] == 'Different' for col in all_columns), axis=1)

            # Update counts
            same_count += same_rows.sum()
            diff_count += diff_rows.sum()
            total_count += chunk1.shape[0]  # Use chunk1's shape to count the total rows processed

            # Apply report type filter
            if report_type == "difference":
                diff_chunk = diff_chunk[diff_rows]
            elif report_type == "matched":
                diff_chunk = diff_chunk[same_rows]

            if not diff_chunk.empty:
                if not headers_written:
                    headers = []
                    for col in all_columns:
                        headers.extend([f"{col}_file1", f"{col}_file2", f"{col}_diff"])
                    f.write('<tr>' + ''.join(f'<th>{col}</th>' for col in headers) + '</tr>')
                    headers_written = True

                # Append the differences to the HTML file
                def highlight_differences(val):
                    return 'diff' if val == 'Different' else 'match' if val == 'Same' else 'same'

                # Extract and write the rows to the output file
                for index, row in diff_chunk.iterrows():
                    row_html = '<tr>'
                    for col in all_columns:
                        row_html += f'<td class="same">{row[col + "_file1"]}</td>'
                        row_html += f'<td class="same">{row[col + "_file2"]}</td>'
                        row_html += f'<td class="{highlight_differences(row[col + "_diff"])}">{row[col + "_diff"]}</td>'
                    row_html += '</tr>'
                    f.write(row_html)

        # Write the final part of the HTML file
        f.write('</table>')

        # Write the summary
        f.write('<script>document.getElementById("summary").innerHTML = "Total records: {}<br>Same records: {}<br>Mismatched records: {}";</script>'.format(total_count, same_count, diff_count))
        f.write('</body></html>')

    print(f"Comparison report generated: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare two CSV files and generate an HTML report.')
    parser.add_argument('file1', help='Path to the first CSV file')
    parser.add_argument('file2', help='Path to the second CSV file')
    parser.add_argument('-o', '--output', required=True, help='Path to the output HTML file')
    parser.add_argument('-k', '--key_cols', nargs='*', help='Key columns for identifying rows uniquely', default=[])
    parser.add_argument('-t', '--type', choices=['full', 'difference', 'matched'], default='full', help='Type of report to generate')
    parser.add_argument('-c', '--compare_cols', help='Comma-separated list of columns to compare')

    args = parser.parse_args()

    if not os.path.exists(args.file1) or not os.path.exists(args.file2):
        print("One or both of the input files do not exist.")
        sys.exit(1)

    compare_cols = args.compare_cols.split(",") if args.compare_cols else None

    compare_csv(args.file1, args.file2, args.output, args.key_cols, args.type, compare_cols)
