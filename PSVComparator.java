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

public class PSVComparator {
	public static void main(String[] args) {
	    String file1Path = "d:\\downloads\\data1.psv";
	    String file2Path = "d:\\downloads\\data2.psv";
	    int numLinesToSkip = 2; // Specify the number of lines to skip

	    List<CSVRecord> records1 = readPSV(file1Path, numLinesToSkip);
	    List<CSVRecord> records2 = readPSV(file2Path, numLinesToSkip);

	    generateHTMLReport(file1Path, file2Path, records1, records2);
	}

	private static List<CSVRecord> readPSV(String filePath, int numLinesToSkip) {
	    try (FileReader reader = new FileReader(filePath);
	         CSVParser parser = CSVFormat.DEFAULT.withDelimiter('|').withTrim().parse(reader)) {
	        List<CSVRecord> records = parser.getRecords();
	        
	        // Check if there are enough lines to skip
	        if (numLinesToSkip > 0 && records.size() > numLinesToSkip) {
	            return records.subList(numLinesToSkip, records.size());
	        } else {
	            return records;
	        }
	    } catch (IOException e) {
	        e.printStackTrace();
	        return null;
	    }
	}

    private static void generateHTMLReport(String file1Path, String file2Path, List<CSVRecord> records1, List<CSVRecord> records2) {
        try (FileWriter writer = new FileWriter("d:\\downloads\\report.html")) {
            Document doc = Jsoup.parse("<html></html>");

            Element style = doc.createElement("style");
            style.text(".table {border-collapse: collapse; width: 100%;}" +
                    ".table th {border: 1px solid #dddddd; text-align: left; padding: 4px; word-wrap: break-word; font-size: 12px;}" +
                    ".table td {border: 1px solid #dddddd; text-align: left; padding: 4px; word-wrap: break-word; font-size: 12px;}" +
                    ".table tr:nth-child(even) {background-color: #f2f2f2;}" +
                    ".different {background-color: #ff9999;}" +
                    ".summary {font-weight: bold;}" +
                    ".summary-table {margin-top: 20px;}" +
                    ".index-col {width: 50px;}" +
                    ".data-col {width: 150px;}" +
                    "@media (max-width: 768px) {.table td, .table th {padding: 2px; font-size: 10px;}}" +
                    ".filter-box {margin-bottom: 10px;}" +
                    ".filter-box select {width: 100%; padding: 5px;}" +
                    ".filter-box p {margin-top: 5px;}");
            doc.head().appendChild(style);

            Element script = doc.createElement("script");
            script.attr("type", "text/javascript");
            script.text(
                "function filterTable() {" +
                "  var filter, table, tr, td, i, visibleRowCount = 0;" +
                "  filter = document.getElementById('filterSelect').value;" +
                "  table = document.getElementById('comparisonTable');" +
                "  tr = table.getElementsByTagName('tr');" +
                "  for (i = 1; i < tr.length; i++) {" +
                "    tr[i].style.display = '';" +
                "    var indexCell = tr[i].getElementsByTagName('td')[0];" +
                "    if (indexCell) {" +
                "      var isDifferent = tr[i].classList.contains('different');" +
                "      if ((filter === 'Matched' && !isDifferent) || (filter === 'Mismatched' && isDifferent) || (filter === 'All')) {" +
                "        visibleRowCount++;" +
                "      } else {" +
                "        tr[i].style.display = 'none';" +
                "      }" +
                "    }" +
                "  }" +
                "  document.getElementById('differentRowCount').textContent = 'Different Rows: ' + visibleRowCount;" +
                "}" +
                "function clearFilter() {" +
                "  document.getElementById('filterSelect').value = 'All';" +
                "  filterTable();" +
                "}"
            );
            doc.head().appendChild(script);

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

            Element filterBox = doc.createElement("div");
            filterBox.addClass("filter-box");
            filterBox.html(
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

            Element comparisonTable = doc.createElement("table");
            comparisonTable.addClass("table");
            comparisonTable.attr("id", "comparisonTable");

            Element tableHeaderRow = doc.createElement("tr");
            Element indexHeader = doc.createElement("th");
            indexHeader.text("Index");
            indexHeader.addClass("index-col");
            tableHeaderRow.appendChild(indexHeader);

            if (!records1.isEmpty()) {
                for (int i = 1; i <= records1.get(0).size(); i++) {
                    Element columnHeader = doc.createElement("th");
                    columnHeader.text("Column " + i);
                    columnHeader.addClass("data-col");
                    tableHeaderRow.appendChild(columnHeader);
                }
            } else if (!records2.isEmpty()) {
                for (int i = 1; i <= records2.get(0).size(); i++) {
                    Element columnHeader = doc.createElement("th");
                    columnHeader.text("Column " + i);
                    columnHeader.addClass("data-col");
                    tableHeaderRow.appendChild(columnHeader);
                }
            }
            comparisonTable.appendChild(tableHeaderRow);

            for (int i = 0; i < Math.max(records1.size(), records2.size()); i++) {
                Element tr = doc.createElement("tr");

                Element indexCell = doc.createElement("td");
                indexCell.text(String.valueOf(i + 1));
                indexCell.addClass("index-col");
                tr.appendChild(indexCell);

                boolean isMismatched = false;

                if (i < records1.size() && i < records2.size()) {
                    isMismatched = createTableCell(doc, tr, records1.get(i).iterator(), records2.get(i).iterator());
                } else if (i < records1.size()) {
                    isMismatched = createTableCell(doc, tr, records1.get(i).iterator(), null);
                } else {
                    isMismatched = createTableCell(doc, tr, null, records2.get(i).iterator());
                }

                if (isMismatched) {
                    indexCell.addClass("different");
                }

                comparisonTable.appendChild(tr);
            }

            doc.body().appendChild(comparisonTable);

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
