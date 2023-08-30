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
import java.util.Iterator;
import java.util.List;

public class CSVComparator {
    public static void main(String[] args) {
        String file1Path = "d:\\downloads\\addresses1.csv";
        String file2Path = "d:\\downloads\\addresses2.csv";

        List<CSVRecord> records1 = readCSV(file1Path);
        List<CSVRecord> records2 = readCSV(file2Path);

        generateHTMLReport(file1Path, file2Path, records1, records2);
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

    private static void generateHTMLReport(String file1Path, String file2Path, List<CSVRecord> records1, List<CSVRecord> records2) {
        try (FileWriter writer = new FileWriter("d:\\downloads\\report.html")) {
            // Create an HTML document
            Document doc = Jsoup.parse("<html></html>");

            // Create a style element for CSS
            Element style = doc.createElement("style");
         // Add CSS styles for table
            style.text(".table {border-collapse: collapse; width: 100%; table-layout: fixed;}" +
                ".table td, .table th {border: 1px solid #dddddd; text-align: left; padding: 4px; word-wrap: break-word; font-size: 12px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; max-width: 200px;}" +
                ".table th {background-color: #f2f2f2;}" +
                ".table tr:nth-child(even) {background-color: #f2f2f2;}" +
                ".different {background-color: #ff9999;}" +
                ".summary {font-weight: bold;}" +
                ".summary-table {margin-top: 20px;}" +
                "@media (max-width: 768px) {" +
                ".table td, .table th {padding: 2px; font-size: 10px;}" +
                "}");

            doc.head().appendChild(style);

            // Add file names and summary
            Element header = doc.createElement("h2");
            header.text("Comparison Report: " + file1Path + " vs. " + file2Path);
            doc.body().appendChild(header);

            Element summary = doc.createElement("p");
            summary.addClass("summary");

            int matchedRecords = countMatchedRecords(records1, records2);
            int mismatchedRecords = countMismatchedRecords(records1, records2);

            summary.text("Summary:\n" +
                    "Matched Records: " + matchedRecords + "\n" +
                    "Mismatched Records: " + mismatchedRecords + "\n" +
                    "Total Records in " + file1Path + ": " + records1.size() + "\n" +
                    "Total Records in " + file2Path + ": " + records2.size());
            doc.body().appendChild(summary);

            // Create a summary table
            Element summaryTable = doc.createElement("table");
            summaryTable.addClass("table summary-table");

            Element summaryTableHeaderRow = doc.createElement("tr");
            Element summaryTableHeaderCell1 = doc.createElement("th");
            Element summaryTableHeaderCell2 = doc.createElement("th");
            summaryTableHeaderCell1.text("File");
            summaryTableHeaderCell2.text("Record Count");
            summaryTableHeaderRow.appendChild(summaryTableHeaderCell1);
            summaryTableHeaderRow.appendChild(summaryTableHeaderCell2);
            summaryTable.appendChild(summaryTableHeaderRow);

            Element file1SummaryRow = doc.createElement("tr");
            Element file1SummaryCell1 = doc.createElement("td");
            Element file1SummaryCell2 = doc.createElement("td");
            file1SummaryCell1.text(file1Path);
            file1SummaryCell2.text(String.valueOf(records1.size()));
            file1SummaryRow.appendChild(file1SummaryCell1);
            file1SummaryRow.appendChild(file1SummaryCell2);
            summaryTable.appendChild(file1SummaryRow);

            Element file2SummaryRow = doc.createElement("tr");
            Element file2SummaryCell1 = doc.createElement("td");
            Element file2SummaryCell2 = doc.createElement("td");
            file2SummaryCell1.text(file2Path);
            file2SummaryCell2.text(String.valueOf(records2.size()));
            file2SummaryRow.appendChild(file2SummaryCell1);
            file2SummaryRow.appendChild(file2SummaryCell2);
            summaryTable.appendChild(file2SummaryRow);

            doc.body().appendChild(summaryTable);

            // Create a table for side-by-side comparison
            Element comparisonTable = doc.createElement("table");
            comparisonTable.addClass("table");

            // Add the index column header
            Element indexHeader = doc.createElement("th");
            indexHeader.text("Index");
            comparisonTable.appendChild(indexHeader);

            // Iterate through rows and columns to create the side-by-side view
            for (int i = 0; i < Math.max(records1.size(), records2.size()); i++) {
                Element tr = doc.createElement("tr");

                // Add the index column
                Element indexCell = doc.createElement("td");
                indexCell.text(String.valueOf(i + 1)); // Index is 1-based
                tr.appendChild(indexCell);

                boolean isMismatched = false; // Flag to track if there's a mismatch in this row

                if (i < records1.size() && i < records2.size()) {
                    isMismatched = createTableCell(doc, tr, records1.get(i).iterator(), records2.get(i).iterator());
                } else if (i < records1.size()) {
                    isMismatched = createTableCell(doc, tr, records1.get(i).iterator(), null);
                } else {
                    isMismatched = createTableCell(doc, tr, null, records2.get(i).iterator());
                }

                // Highlight the index column if there is a mismatch
                if (isMismatched) {
                    indexCell.addClass("different");
                }

                comparisonTable.appendChild(tr);
            }

            doc.body().appendChild(comparisonTable);

            // Write the HTML document to the file
            writer.write(doc.outerHtml());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static boolean createTableCell(Document doc, Element tr, Iterator<String> values1, Iterator<String> values2) {
        boolean isMismatched = false;
        
        while (values1 != null && values1.hasNext() || values2 != null && values2.hasNext()) {
            String value1 = values1 != null && values1.hasNext() ? values1.next() : "Not Found";
            String value2 = values2 != null && values2.hasNext() ? values2.next() : "Not Found";

            Element td = doc.createElement("td");
            if (!value1.equals(value2)) {
                td.addClass("different");
                isMismatched = true;
            }
            Element pre = doc.createElement("pre");
            pre.appendText("Left: " + value1 + "\nRight: " + value2 + "\n");
            td.appendChild(pre);
            tr.appendChild(td);
        }
        
        return isMismatched;
    }


    private static int countMatchedRecords(List<CSVRecord> records1, List<CSVRecord> records2) {
        int count = 0;
        for (CSVRecord record1 : records1) {
            for (CSVRecord record2 : records2) {
                if (record1.equals(record2)) {
                    count++;
                    break; // Move to the next record in records1
                }
            }
        }
        return count;
    }

    private static int countMismatchedRecords(List<CSVRecord> records1, List<CSVRecord> records2) {
        int count = 0;
        for (int i = 0; i < Math.min(records1.size(), records2.size()); i++) {
            if (!records1.get(i).equals(records2.get(i))) {
                count++;
            }
        }
        return count;
    }
}
