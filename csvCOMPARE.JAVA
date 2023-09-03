package Accessibility.Automation;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

public class CSVComparator {
    public static void main(String[] args) {
        String file1Path = "D:\\Downloads\\addresses1.csv";
        String file2Path = "D:\\Downloads\\addresses2.csv";
        int[] keyColumnIndices = {0}; // Set the indices of the key columns (0-based index)

        List<CSVRecord> records1 = readCSV(file1Path);
        List<CSVRecord> records2 = readCSV(file2Path);

        generateHTMLReport(file1Path, file2Path, records1, records2, keyColumnIndices);
    }

    private static List<CSVRecord> readCSV(String filePath) {
        try (FileReader reader = new FileReader(filePath);
             CSVParser parser = CSVFormat.DEFAULT.withTrim().parse(reader)) {
            return parser.getRecords();
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    private static void generateHTMLReport(String file1Path, String file2Path, List<CSVRecord> records1, List<CSVRecord> records2, int[] keyColumnIndices) {
        try (FileWriter writer = new FileWriter("D:\\Downloads\\comparison_report.html")) {
            // Create an HTML document
            Document doc = Jsoup.parse("<html></html>");

            // Create a style element for CSS
            Element style = doc.createElement("style");
            style.text(".table {border-collapse: collapse; width: 100%;}" +
                    ".table th {border: 1px solid #dddddd; text-align: left; padding: 4px; word-wrap: break-word; font-size: 12px;}" +
                    ".table td {border: 1px solid #dddddd; text-align: left; padding: 4px; word-wrap: break-word; font-size: 12px;}" +
                    ".table tr:nth-child(even) {background-color: #f2f2f2;}" +
                    ".different {background-color: #ff9999; animation: blinker 1s linear infinite;}" + // Add the blinking effect
                    ".summary {font-weight: bold;}" +
                    ".summary-table {margin-top: 20px;}" +
                    ".index-col {width: 50px;}" + // Fixed width for the index column
                    ".data-col {width: 150px;}" + // Fixed width for data columns
                    "@media (max-width: 768px) {" +
                    ".table td, .table th {padding: 2px; font-size: 10px;}" +
                    "}" +
                    "@keyframes blinker {" + // Keyframes for the blinking effect
                    "    70%, 100% {" +
                    "        opacity: 1; /* Fully visible */" +
                    "    }" +
                    "    90% {" +
                    "        opacity: 0.6; /* Fully invisible */" +
                    "    }" +
                    "}");
            doc.head().appendChild(style);

            // Add filter dropdown and JavaScript
            Element filterBox = doc.createElement("div");
            filterBox.addClass("filter-box");
            filterBox.html(
                    "<label for='filterSelect'>Filter by:</label>" +
                            "<select id='filterSelect' onchange='filterTable()'>" +
                            "<option value='All'>All</option>" +
                            "<option value='Matched'>Matched</option>" +
                            "<option value='Mismatched'>Mismatched</option>" +
                            "</select>" +
                            "<p id='rowCountCaption'></p>" +
                            "<script>" +
                            "function filterTable() {" +
                            "  var filter, table, tr, td, i, visibleRowCount = 0, rowCountCaption = 'Total Rows: ';" +
                            "  filter = document.getElementById('filterSelect').value;" +
                            "  table = document.getElementById('comparisonTable');" +
                            "  tr = table.getElementsByTagName('tr');" +
                            "  for (i = 1; i < tr.length; i++) {" +
                            "    tr[i].style.display = '';" +
                            "    var indexCell = tr[i].getElementsByTagName('td')[0];" +
                            "    if (indexCell) {" +
                            "      var isDifferent = indexCell.classList.contains('different');" +
                            "      if ((filter === 'Matched' && !isDifferent) || (filter === 'Mismatched' && isDifferent) || (filter === 'All')) {" +
                            "        visibleRowCount++;" +
                            "      } else {" +
                            "        tr[i].style.display = 'none';" +
                            "      }" +
                            "    }" +
                            "  }" +
                            "  if (filter === 'All') {" +
                            "    rowCountCaption = 'Total Rows: ' + (tr.length - 1);" +
                            "  } else if (filter === 'Matched') {" +
                            "    rowCountCaption = 'Matched Rows: ' + visibleRowCount;" +
                            "  } else {" +
                            "    rowCountCaption = 'Different Rows: ' + visibleRowCount;" +
                            "  }" +
                            "  document.getElementById('rowCountCaption').textContent = rowCountCaption;" +
                            "}" +
                            "function clearFilter() {" +
                            "  document.getElementById('filterSelect').value = 'All';" +
                            "  filterTable();" +
                            "}" +
                            "function initializeFilter() {" +
                            "  filterTable();" +
                            "}" +
                            "initializeFilter();" +
                            "</script>"
            );
            doc.body().appendChild(filterBox);

            // Add file names and summary
            Element header = doc.createElement("h2");
            header.text("Comparison Report: " + file1Path + " vs. " + file2Path);
            doc.body().appendChild(header);

            Element summary = doc.createElement("p");
            summary.addClass("summary");

            int matchedRecords = calculateMatchedRowCount(records1, records2, keyColumnIndices);
            int differentRecords = calculateDifferentRowCount(records1, records2, keyColumnIndices);

            // Create a summary table
            Element summaryTable = doc.createElement("table");
            summaryTable.addClass("table summary-table");

            // Add a table header row with column names
            Element summaryTableHeaderRow = doc.createElement("tr");
            Element typeOfFileHeader = doc.createElement("th");
            Element fileNameHeader = doc.createElement("th");
            Element recordCountHeader = doc.createElement("th");

            typeOfFileHeader.text("Type of File");
            fileNameHeader.text("File Name");
            recordCountHeader.text("Record Count");

            summaryTableHeaderRow.appendChild(typeOfFileHeader);
            summaryTableHeaderRow.appendChild(fileNameHeader);
            summaryTableHeaderRow.appendChild(recordCountHeader);
            summaryTable.appendChild(summaryTableHeaderRow);

            // Add the Baseline file entry
            Element file1SummaryRow = doc.createElement("tr");
            Element baselineCell = doc.createElement("td");
            Element file1NameCell = doc.createElement("td");
            Element file1RecordCountCell = doc.createElement("td");

            baselineCell.text("Baseline"); // Type of File
            file1NameCell.text(file1Path); // File Name
            file1RecordCountCell.text(String.valueOf(records1.size())); // Record Count

            file1SummaryRow.appendChild(baselineCell);
            file1SummaryRow.appendChild(file1NameCell);
            file1SummaryRow.appendChild(file1RecordCountCell);
            summaryTable.appendChild(file1SummaryRow);

            // Add the Current file entry
            Element file2SummaryRow = doc.createElement("tr");
            Element currentCell = doc.createElement("td");
            Element file2NameCell = doc.createElement("td");
            Element file2RecordCountCell = doc.createElement("td");

            currentCell.text("Current"); // Type of File
            file2NameCell.text(file2Path); // File Name
            file2RecordCountCell.text(String.valueOf(records2.size())); // Record Count

            file2SummaryRow.appendChild(currentCell);
            file2SummaryRow.appendChild(file2NameCell);
            file2SummaryRow.appendChild(file2RecordCountCell);
            summaryTable.appendChild(file2SummaryRow);

            doc.body().appendChild(summaryTable);

            // Create a table for side-by-side comparison
            Element comparisonTable = doc.createElement("table");
            comparisonTable.addClass("table");
            comparisonTable.attr("id", "comparisonTable"); // Add an ID for filtering

            // Add the table header row with column names
            Element tableHeaderRow = doc.createElement("tr");
            Element indexHeader = doc.createElement("th");
            indexHeader.text("Index");
            indexHeader.addClass("index-col"); // Apply the class for fixed width
            tableHeaderRow.appendChild(indexHeader);

            // Add headers for data columns
            for (int i = 1; i <= Math.max(records1.get(0).size(), records2.get(0).size()); i++) {
                Element columnHeader = doc.createElement("th");
                columnHeader.text("Column " + i);
                columnHeader.addClass("data-col"); // Apply the class for fixed width
                tableHeaderRow.appendChild(columnHeader);
            }
            comparisonTable.appendChild(tableHeaderRow);

            // Create maps to store records based on the key columns
            Map<List<String>, CSVRecord> recordMap1 = new HashMap<>();
            Map<List<String>, CSVRecord> recordMap2 = new HashMap<>();

            for (CSVRecord record : records1) {
                List<String> key = new ArrayList<>();
                for (int keyColumnIndex : keyColumnIndices) {
                    if (record.size() > keyColumnIndex) {
                        key.add(record.get(keyColumnIndex));
                    }
                }
                recordMap1.put(key, record);
            }

            for (CSVRecord record : records2) {
                List<String> key = new ArrayList<>();
                for (int keyColumnIndex : keyColumnIndices) {
                    if (record.size() > keyColumnIndex) {
                        key.add(record.get(keyColumnIndex));
                    }
                }
                recordMap2.put(key, record);
            }

            // Iterate through all unique keys from both files
            Set<List<String>> allKeys = new HashSet<>(recordMap1.keySet());
            allKeys.addAll(recordMap2.keySet());

            int rowIndex = 1;
            for (List<String> key : allKeys) {
                Element tr = doc.createElement("tr");

                // Add the index column
                Element indexCell = doc.createElement("td");
                indexCell.text(String.valueOf(rowIndex));
                indexCell.addClass("index-col"); // Apply the class for fixed width
                tr.appendChild(indexCell);

                boolean isMismatched = false; // Flag to track if there's a mismatch in this row

                CSVRecord record1 = recordMap1.get(key);
                CSVRecord record2 = recordMap2.get(key);

                if (record1 != null && record2 != null) {
                    isMismatched = createTableCell(doc, tr, record1.iterator(), record2.iterator());
                } else {
                    // Handle the case where the key is in one file but not in the other
                    isMismatched = true;
                    if (record1 != null) {
                        createNotFoundCell(doc, tr, record1, "Current");
                    } else if (record2 != null) {
                        createNotFoundCell(doc, tr, record2, "Baseline");
                    } else {
                        createNotFoundCell(doc, tr, null, "Both");
                    }
                }

                // Highlight the index column if there is a mismatch
                if (isMismatched) {
                    indexCell.addClass("different");
                }

                tr.addClass(isMismatched ? "mismatched" : "matched");
                tr.addClass("data-row");
                comparisonTable.appendChild(tr);
                rowIndex++;
            }

            doc.body().appendChild(comparisonTable);

            // Write the HTML document to the file
            writer.write(doc.outerHtml());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void createNotFoundCell(Document doc, Element tr, CSVRecord record, String side) {
        // Create a cell for each value in the record
        for (String value : record) {
            Element td = doc.createElement("td");
            td.addClass("different");

            // Set the cell text based on the side
            if ("Current".equals(side)) {
                td.text("Key not found in Current file");
                Element pre = doc.createElement("pre");
                pre.text("Baseline: " + value);
                td.appendChild(pre);
            } else if ("Baseline".equals(side)) {
                td.text("Key not found in Baseline file");
                Element pre = doc.createElement("pre");
                pre.text("Current: " + value);
                td.appendChild(pre);
            } else {
                td.text("Key not found in Both files");
            }

            tr.appendChild(td);
        }
    }

    private static boolean createTableCell(Document doc, Element tr, Iterator<String> values1, Iterator<String> values2) {
        boolean isMismatched = false;

        while (values1.hasNext() || values2.hasNext()) {
            String value1 = values1.hasNext() ? values1.next() : "";
            String value2 = values2.hasNext() ? values2.next() : "";

            Element td = doc.createElement("td");
            if (!value1.equals(value2)) {
                td.addClass("different");
                isMismatched = true;
            }
            Element pre = doc.createElement("pre");
            pre.appendText("Baseline: " + value1 + "\nCurrent: " + value2 + "\n");
            td.appendChild(pre);
            tr.appendChild(td);
        }

        return isMismatched;
    }

    private static int calculateMatchedRowCount(List<CSVRecord> records1, List<CSVRecord> records2, int[] keyColumnIndices) {
        int count = 0;
        Map<List<String>, CSVRecord> recordMap2 = new HashMap<>();

        for (CSVRecord record : records2) {
            List<String> key = new ArrayList<>();
            for (int keyColumnIndex : keyColumnIndices) {
                if (record.size() > keyColumnIndex) {
                    key.add(record.get(keyColumnIndex));
                }
            }
            recordMap2.put(key, record);
        }

        for (CSVRecord record : records1) {
            List<String> key = new ArrayList<>();
            for (int keyColumnIndex : keyColumnIndices) {
                if (record.size() > keyColumnIndex) {
                    key.add(record.get(keyColumnIndex));
                }
            }
            CSVRecord correspondingRecord = recordMap2.get(key);
            if (correspondingRecord != null && record.equals(correspondingRecord)) {
                count++;
            }
        }

        return count;
    }

    private static int calculateDifferentRowCount(List<CSVRecord> records1, List<CSVRecord> records2, int[] keyColumnIndices) {
        int count = 0;
        Map<List<String>, CSVRecord> recordMap2 = new HashMap<>();

        for (CSVRecord record : records2) {
            List<String> key = new ArrayList<>();
            for (int keyColumnIndex : keyColumnIndices) {
                if (record.size() > keyColumnIndex) {
                    key.add(record.get(keyColumnIndex));
                }
            }
            recordMap2.put(key, record);
        }

        for (CSVRecord record : records1) {
            List<String> key = new ArrayList<>();
            for (int keyColumnIndex : keyColumnIndices) {
                if (record.size() > keyColumnIndex) {
                    key.add(record.get(keyColumnIndex));
                }
            }
            CSVRecord correspondingRecord = recordMap2.get(key);
            if (correspondingRecord == null || !record.equals(correspondingRecord)) {
                count++;
            }
        }

        return count;
    }
}
