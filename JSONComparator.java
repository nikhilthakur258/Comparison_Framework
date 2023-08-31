package Accessibility.Automation;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.text.StringEscapeUtils;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

public class JSONComparator {

    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Usage: java JSONComparator <jsonFile1> <jsonFile2>");
            return;
        }

        String jsonFile1 = args[0];
        String jsonFile2 = args[1];

        compareJSON(jsonFile1, jsonFile2);
    }

    private static String getTableCellHtml(String content, String status) {
        // Highlight only the "Different" status cell in red
        String cellClass = "status-cell";
        if ("Different".equals(status)) {
            cellClass += " different-status";
        }
        return "<td class='" + cellClass + "' style='word-wrap: break-word;'>" + StringEscapeUtils.escapeHtml4(content) + "</td>";
    }

    public static void compareJSON(String jsonFile1, String jsonFile2) {
        try {
            JsonNode node1 = objectMapper.readTree(new File(jsonFile1));
            JsonNode node2 = objectMapper.readTree(new File(jsonFile2));

            List<Map.Entry<String, JsonNode>> entries1 = flattenJSON(node1, "");
            List<Map.Entry<String, JsonNode>> entries2 = flattenJSON(node2, "");
            Set<String> allKeys = new HashSet<>();

            for (Map.Entry<String, JsonNode> entry : entries1) {
                allKeys.add(entry.getKey());
            }
            for (Map.Entry<String, JsonNode> entry : entries2) {
                allKeys.add(entry.getKey());
            }

            List<String> statuses = new ArrayList<>(); // Store the status for each row

            StringBuilder reportBuilder = new StringBuilder();
            reportBuilder.append("<html><head><style>")
                    .append("table {border-collapse: collapse; table-layout: fixed; width: 100%;}")
                    .append("th, td {text-align: left; padding: 8px; word-wrap: break-word;}")
                    .append("th {background-color: #4CAF50; color: white;}")
                    .append("tr:nth-child(even) {background-color: #f2f2f2;}")
                    .append(".different-status {background-color: red; color: white;}")
                    .append(".status-cell {white-space: nowrap;}")  // To prevent status cell content from wrapping
                    .append("</style></head><body>")
                    .append("<h1>Comparison Report</h1>");

            // Filter options for keys and statuses
            reportBuilder.append("<form>")
                    .append("<select id='keyFilter' onchange='filterTable()'>") // Add ID 'keyFilter'
                    .append("<option value=''>All</option>");
            for (String key : allKeys) {
                reportBuilder.append("<option value='").append(key).append("'>").append(key).append("</option>");
            }
            reportBuilder.append("</select>");

            reportBuilder.append("<select id='statusFilter' onchange='filterTable()'>") // Add ID 'statusFilter'
                    .append("<option value=''>All</option>")
                    .append("<option value='Same'>Same</option>")
                    .append("<option value='Different'>Different</option>")
                    .append("<option value='Not found'>Not found</option>")
                    .append("</select>");

            // Add a "Reset Filters" button
            reportBuilder.append("<button onclick='resetFilters()'>Reset Filters</button>");

            reportBuilder.append("</form>");

            // Table headers
            reportBuilder.append("<table id='comparisonTable'>")
                    .append("<thead class='table-header'><tr><th>Key</th><th>Value 1</th><th>Value 2</th><th>Status</th></tr></thead>");

            // Table body
            reportBuilder.append("<tbody>");

            for (String key : allKeys) {
                String value1 = getNestedValue(entries1, key);
                String value2 = getNestedValue(entries2, key);
                String status = "";

                if (value1 != null && value2 != null) {
                    if (value1.equals(value2)) {
                        status = "Same";
                    } else {
                        status = "Different";
                    }
                } else if (value1 == null && value2 == null) {
                    status = "Not found";
                } else {
                    status = "Different";
                }

                statuses.add(status); // Add the status to the list

                reportBuilder.append("<tr class='").append(key).append("'>")
                        .append("<td>").append(StringEscapeUtils.escapeHtml4(key)).append("</td>")
                        .append(getTableCellHtml(value1, status))
                        .append(getTableCellHtml(value2, status))
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
                    .append("for (var i = 1; i < rows.length; i++) {") // Start from 1 to skip the header row
                    .append("var row = rows[i];")
                    .append("var key = row.cells[0].textContent.trim();")
                    .append("var status = row.cells[3].textContent.trim();")
                    .append("var hideRow = (keyFilter !== '' && key !== keyFilter) || (statusFilter !== '' && status !== statusFilter);")
                    .append("row.style.display = hideRow ? 'none' : '';")
                    .append("}")
                    .append("}")

                    // Add a function to reset filters and show all rows
                    .append("function resetFilters() {")
                    .append("document.getElementById('keyFilter').value = '';")
                    .append("document.getElementById('statusFilter').value = '';")
                    .append("var table = document.getElementById('comparisonTable');")
                    .append("var rows = table.getElementsByTagName('tr');")
                    .append("for (var i = 1; i < rows.length; i++) {") // Start from 1 to skip the header row
                    .append("var row = rows[i];")
                    .append("row.style.display = '';")
                    .append("}")
                    .append("}")
                    .append("</script>")
                    .append("</body></html>");

            String report = reportBuilder.toString();

            // Create the "results" folder if it doesn't exist
            File resultsFolder = new File("results");
            if (!resultsFolder.exists()) {
                resultsFolder.mkdirs();
            }

            // Save the HTML report to a file
            String filePath = "results/comparison_report.html";
            FileWriter fileWriter = new FileWriter(filePath);
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

    private static List<Map.Entry<String, JsonNode>> flattenJSON(JsonNode node, String prefix) {
        List<Map.Entry<String, JsonNode>> entries = new ArrayList<>();
        if (node.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> fields = node.fields();
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> entry = fields.next();
                String key = entry.getKey();
                JsonNode value = entry.getValue();
                String newPrefix = prefix.isEmpty() ? key : prefix + "." + key;
                if (value.isValueNode()) {
                    entries.add(new AbstractMap.SimpleEntry<>(newPrefix, value));
                } else if (value.isObject() || value.isArray()) {
                    entries.addAll(flattenJSON(value, newPrefix));
                }
            }
        }
        return entries;
    }
}
