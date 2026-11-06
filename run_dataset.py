import csv
import os
import re
import time
from typing import List
from schema import ExtractedDocument
from retry_loop import extract_with_retry


def load_dataset_file(filepath: str) -> List[str]:
    """Reads a dataset file and splits strictly on lines containing only '---'."""
    if not os.path.exists(filepath):
        print(f"Warning: File '{filepath}' not found.")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split strictly on lines consisting only of '---' (ignoring surrounding spaces)
    raw_entries = re.split(r"^\s*---\s*$", content, flags=re.MULTILINE)
    entries = [entry.strip() for entry in raw_entries if entry.strip()]
    return entries


def process_dataset():
    # File list containing your 3 dataset files
    dataset_files = [
        "Dataset\\invoices_final.txt",
        "Dataset\\RealDataset_final.txt",
        "Dataset\\utility_bills_final.txt",
        "Dataset\\edge_case_standardized.txt"
    ]

    all_entries = []
    for file_path in dataset_files:
        entries = load_dataset_file(file_path)
        all_entries.extend([(file_path, entry) for entry in entries])

    if not all_entries:
        print(
            "No entries found. Make sure your dataset .txt files exist in this folder."
        )
        return

    print(f"Found {len(all_entries)} total dataset entries to process.\n")

    # CSV log output settings
    csv_filename = "extraction_results.csv"
    fieldnames = [
        "source_file",
        "entry_id",
        "status",
        "biller_name",
        "document_type",
        "document_date",
        "total_amount",
        "currency",
        "summary",
        "error_reason",
    ]

    with open(csv_filename, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        passed_count = 0
        failed_count = 0

        for index, (source_file, text) in enumerate(all_entries, start=1):
            print(
                f"Processing Entry {index}/{len(all_entries)} from {source_file}..."
            )

            try:
                # Run structured extraction with retries
                result: ExtractedDocument = extract_with_retry(
                    text, max_retries=3
                )

                if result:
                    writer.writerow(
                        {
                            "source_file": source_file,
                            "entry_id": index,
                            "status": "PASS",
                            "biller_name": result.biller_name,
                            "document_type": result.document_type,
                            "document_date": result.document_date,
                            "total_amount": result.total_amount,
                            "currency": result.currency,
                            "summary": result.summary,
                            "error_reason": "",
                        }
                    )
                    passed_count += 1
                    print(f"--> Result: PASS")
                else:
                    writer.writerow(
                        {
                            "source_file": source_file,
                            "entry_id": index,
                            "status": "FAIL",
                            "biller_name": "",
                            "document_type": "",
                            "document_date": "",
                            "total_amount": "",
                            "currency": "",
                            "summary": "",
                            "error_reason": "Failed Pydantic validation after max retries",
                        }
                    )
                    failed_count += 1
                    print(f"--> Result: FAIL (Validation Failed)")

            except Exception as e:
                writer.writerow(
                    {
                        "source_file": source_file,
                        "entry_id": index,
                        "status": "FAIL",
                        "biller_name": "",
                        "document_type": "",
                        "document_date": "",
                        "total_amount": "",
                        "currency": "",
                        "summary": "",
                        "error_reason": str(e),
                    }
                )
                failed_count += 1
                print(f"--> Result: FAIL ({e})")

            # Pause 15 seconds between requests to comply with 5 RPM Free Tier quota
            if index < len(all_entries):
                print("Waiting 15 seconds to respect rate limits...")
                time.sleep(15)

    print("\n--- Processing Complete ---")
    print(f"Total Processed: {len(all_entries)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Results saved to: {csv_filename}")


if __name__ == "__main__":
    process_dataset()