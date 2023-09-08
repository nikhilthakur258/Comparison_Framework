package Accessibility.Automation;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.text.StringEscapeUtils;

import java.io.*;
import java.util.*;

public class JSONComparator {

    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static void main(String[] args) {
        if (args.length != 3) {
            System.out.println("Usage: java JSONComparator <jsonFile1> <jsonFile2> <jsonFile3>");
            return;
        }

        String jsonFile1 = args[0];
        String jsonFile2 = args[1];
        String jsonFile3 = args[2];

        compareJSON(jsonFile1, jsonFile2, jsonFile3);
    }

    private static String getTableCellHtml(String content, String status) {
        String cellClass = "";
        if ("Different".equals(status) || "Not found".equals(status)) {
            cellClass = "different-status";
        }
        return "<td class='" + cellClass + "' style='word-wrap: break-word;'>" + StringEscapeUtils.escapeHtml4(content) + "</td>";
    }

    public static void compareJSON(String jsonFile1, String jsonFile2, String jsonFile3) {
        try {
            String reportFilePath = "results/comparison_report.html";

            // Read the existing report content if it exists
            StringBuilder existingReportContent = new StringBuilder();
            boolean reportExists = new File(reportFilePath).exists();
            if (reportExists) {
                Scanner scanner = new Scanner(new File(reportFilePath));
                while (scanner.hasNextLine()) {
                    existingReportContent.append(scanner.nextLine());
                }
                scanner.close();
            }

            // Extract the file names without extensions
            String fileName1 = new File(jsonFile1).getName().replaceFirst("[.][^.]+$", "");
            String fileName2 = new File(jsonFile2).getName().replaceFirst("[.][^.]+$", "");
            String fileName3 = new File(jsonFile3).getName().replaceFirst("[.][^.]+$", "");

            JsonNode node1 = objectMapper.readTree(new File(jsonFile1));
            JsonNode node2 = objectMapper.readTree(new File(jsonFile2));
            JsonNode node3 = objectMapper.readTree(new File(jsonFile3));

            List<Map.Entry<String, JsonNode>> entries1 = flattenJSON(node1);
            List<Map.Entry<String, JsonNode>> entries2 = flattenJSON(node2);
            List<Map.Entry<String, JsonNode>> entries3 = flattenJSON(node3);
            Set<String> allKeys = new HashSet<>();

            for (Map.Entry<String, JsonNode> entry : entries1) {
                allKeys.add(entry.getKey());
            }
            for (Map.Entry<String, JsonNode> entry : entries2) {
                allKeys.add(entry.getKey());
            }
            for (Map.Entry<String, JsonNode> entry : entries3) {
                allKeys.add(entry.getKey());
            }

            List<String> statuses = new ArrayList<>(); // Store the status for each row

            StringBuilder reportBuilder = new StringBuilder();

            if (!reportExists) {
                // If the report doesn't exist, create the initial structure
                reportBuilder.append("<html><head><style>")
                        .append("table {border-collapse: collapse; table-layout: fixed; width: 100%;}")
                        .append("th, td {text-align: left; padding: 8px; word-wrap: break-word;}")
                        .append("th {background-color: #4CAF50; color: white;}")
                        .append("tr:nth-child(even) {background-color: #f2f2f2;}")
                        .append(".different-status {background-color: red; color: white;}")
                        .append("</style></head><body>")
                        .append("<h1>Comparison Report</h1>");

                // Add filter options for keys and statuses
                reportBuilder.append("<form>")
                        .append("<select id='keyFilter' onchange='filterTable()'>")
                        .append("<option value=''>All</option>");
                for (String key : allKeys) {
                    reportBuilder.append("<option value='").append(key).append("'>").append(key).append("</option>");
                }
                reportBuilder.append("</select>")
                        .append("<select id='statusFilter' onchange='filterTable()'>")
                        .append("<option value=''>All</option>")
                        .append("<option value='Same'>Same</option>")
                        .append("<option value='Different'>Different</option>")
                        .append("<option value='Not found'>Not found</option>")
                        .append("</select>")
                        .append("<button onclick='resetFilters()'>Reset Filters</button>")
                        .append("<span id='recordCount'></span>") // Add a span for record count
                        .append("</form>");

                // Add table headers
                reportBuilder.append("<table id='comparisonTable'>")
                        .append("<thead class='table-header'><tr><th>File Name</th><th>Key</th><th>Landing zone</th><th>Raw Zone</th><th>Curated Zone</th><th>Status</th></tr></thead>");
            } else {
                // If the report already exists, locate the end of the table to append new rows
                int tableEndIndex = existingReportContent.indexOf("</tbody>");
                if (tableEndIndex != -1) {
                    reportBuilder.append(existingReportContent.substring(0, tableEndIndex)); // Exclude the end of the table
                } else {
                    // If the table end couldn't be found, use the existing content
                    reportBuilder.append(existingReportContent);
                }
            }

            for (String key : allKeys) {
                String value1 = getNestedValue(entries1, key);
                String value2 = getNestedValue(entries2, key);
                String value3 = getNestedValue(entries3, key);
                String status = "";

                if (value1 != null && value2 != null && value3 != null) {
                    if (value1.equals(value2) && value2.equals(value3)) {
                        status = "Same";
                    } else {
                        status = "Different";
                    }
                } else if (value1 == null && value2 == null && value3 == null) {
                    status = "Not found";
                } else {
                    status = "Different";
                }

                statuses.add(status); // Add the status to the list

                reportBuilder.append("<tr class='").append(key).append("'>")
                        .append("<td>").append(fileName1).append(" - ").append(fileName2).append(" - ").append(fileName3).append("</td>")
                        .append("<td>").append(StringEscapeUtils.escapeHtml4(key)).append("</td>")
                        .append(getTableCellHtml(value1, status))
                        .append(getTableCellHtml(value2, status))
                        .append(getTableCellHtml(value3, status))
                        .append("<td>").append(status).append("</td>")
                        .append("</tr>");
            }

            reportBuilder.append("</tbody></table>")
                    .append("<script>")
                    .append("function filterTable() {")
                    .append("var keyFilter = document.getElementById('keyFilter').value;")
                    .append("var statusFilter = document.getElementById('statusFilter').value;")
                    .append("var table = document.getElementById('comparisonTable');")
                    .append("var rows = table.getElementsByTagName('tr');")
                    .append("var recordCount = 0;") // Initialize record count
                    .append("for (var i = 1; i < rows.length; i++) {") // Start from 1 to skip the header row
                    .append("var row = rows[i];")
                    .append("var key = row.cells[1].textContent.trim();")
                    .append("var status = row.cells[5].textContent.trim();")
                    .append("var hideRow = (keyFilter !== '' && key !== keyFilter) || (statusFilter !== '' && status !== statusFilter);")
                    .append("row.style.display = hideRow ? 'none' : '';")
                    .append("if (!hideRow) { recordCount++; }") // Increment record count if row is displayed
                    .append("}")
                    .append("document.getElementById('recordCount').textContent = 'Records: ' + recordCount;") // Update record count
                    .append("}")

                    // Add a function to reset filters and show all rows
                    .append("function resetFilters() {")
                    .append("document.getElementById('keyFilter').value = '';")
                    .append("document.getElementById('statusFilter').value = '';")
                    .append("var table = document.getElementById('comparisonTable');")
                    .append("var rows = table.getElementsByTagName('tr');")
                    .append("var recordCount = 0;") // Initialize record count
                    .append("for (var i = 1; i < rows.length; i++) {") // Start from 1 to skip the header row
                    .append("var row = rows[i];")
                    .append("row.style.display = '';")
                    .append("recordCount++;") // Increment record count for each row
                    .append("}")
                    .append("document.getElementById('recordCount').textContent = 'Records: ' + recordCount;") // Update record count
                    .append("}")
                    .append("</script>")
                    .append("</body></html>");

            String report = reportBuilder.toString();

            // Save the report to the file
            FileWriter fileWriter = new FileWriter(reportFilePath);
            fileWriter.write(report);
            fileWriter.close();

            System.out.println("Comparison report generated successfully!");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static String getNestedValue(List<Map.Entry<String, JsonNode>> entries, String key) {
        for (Map.Entry<String, JsonNode> entry : entries) {
            if (entry.getKey().equals(key)) {
                return entry.getValue().toString();
            }
        }
        return null;
    }

    private static List<Map.Entry<String, JsonNode>> flattenJSON(JsonNode node) {
        List<Map.Entry<String, JsonNode>> entries = new ArrayList<>();
        if (node.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> fields = node.fields();
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> entry = fields.next();
                String key = entry.getKey();
                JsonNode value = entry.getValue();
                if (value.isValueNode()) {
                    entries.add(new AbstractMap.SimpleEntry<>(key, value));
                } else if (value.isObject() || value.isArray()) {
                    entries.addAll(flattenJSON(value));
                }
            }
        }
        return entries;
    }
}
