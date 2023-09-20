import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.File;
import java.io.FileOutputStream;
import java.util.HashMap;
import java.util.Map;

public class XMLtoXLSXConverter {

    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Usage: java XMLtoXLSXConverter input.xml output.xlsx");
            return;
        }

        String inputXmlFile = args[0];
        String outputXlsxFile = args[1];

        try {
            DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
            DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
            Document doc = dBuilder.parse(new File(inputXmlFile));

            Workbook workbook = new XSSFWorkbook();
            Sheet sheet = workbook.createSheet("Data");

            NodeList rootElements = doc.getDocumentElement().getChildNodes();

            int rowNum = 0;

            for (int rootIdx = 0; rootIdx < rootElements.getLength(); rootIdx++) {
                Element rootElement = (Element) rootElements.item(rootIdx);
                NodeList nodeList = rootElement.getChildNodes();
                Map<String, String> data = new HashMap<>();

                for (int i = 0; i < nodeList.getLength(); i++) {
                    if (nodeList.item(i) instanceof Element) {
                        Element node = (Element) nodeList.item(i);
                        data.put(node.getNodeName(), node.getTextContent());
                    }
                }

                Row row = sheet.createRow(rowNum++);
                int cellNum = 0;

                for (Map.Entry<String, String> entry : data.entrySet()) {
                    String key = entry.getKey();
                    String value = entry.getValue();
                    row.createCell(cellNum++).setCellValue(key);
                    row.createCell(cellNum++).setCellValue(value);
                }
            }

            FileOutputStream outputStream = new FileOutputStream(outputXlsxFile);
            workbook.write(outputStream);
            outputStream.close();
            System.out.println("Conversion completed successfully.");
        } catch (Exception e) {
            e.printStackTrace();
            System.err.println("Error during conversion: " + e.getMessage());
        }
    }
}
