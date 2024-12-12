public class DataProcessor {

    private String internalData;
    public int processedCount;

    public DataProcessor(String initialData) {
        this.internalData = initialData;
        this.processedCount = 0;
    }

    public void processData(int iterations) {
        if (internalData == null || internalData.isEmpty()) {
            System.out.println("No data to process.");
            return;
        }

        System.out.println("Starting data processing...");

        for (int i = 0; i < iterations; i++) {
            internalData = performInternalOperation(internalData);
            processedCount++;
            System.out.println("Iteration " + (i + 1) + ": " + internalData);
        }
         System.out.println("Data processing complete. Processed " + processedCount + " times.");
    }

    public void displayProcessedCount() {
        System.out.println("Total processed count: " + processedCount);
    }

    private String performInternalOperation(String data) {
        return data.toUpperCase() + " - Processed";
    }


    public static void main(String[] args) {
        DataProcessor processor = new DataProcessor("initial value");
        processor.processData(3);
        processor.displayProcessedCount();

        DataProcessor processor2 = new DataProcessor("");
        processor2.processData(3);
    }
}
