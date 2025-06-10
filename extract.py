import os
import io
import asyncio
from utils.logger_utils import logger
from utils.s3_utils import S3Utils
import shutil
import glob

# Import your main function
from olmocr.pipeline import main

def initialise_s3(source_system: str):
    if source_system == "disclosure":
        s3_bucket = os.getenv("DISCLOSURE_S3_BUCKET")
    elif source_system == "sed":
        s3_bucket = os.getenv("SED_S3_BUCKET")

    s3 = S3Utils(s3_bucket)
    return s3


async def process_disclosure(doc_url, document_id, source_system):
    s3 = initialise_s3(source_system)
    root_dir = f"repository/disclosure_pdf_extract/{document_id}"
    local_pdf_path = None

    try:
        # Fetch the PDF from S3 to local storage
        local_pdf_path = s3.fetch_file_from_s3(doc_url)
        logger.info(f"Downloaded PDF to: {local_pdf_path}")

        # Set up workspace for the main function
        workspace = f"localworkspace/{document_id}"
        os.makedirs(workspace, exist_ok=True)

        # Call the main function with the local PDF path
        await main(
            workspace=workspace,
            pdfs=[local_pdf_path],  # Pass the local PDF path
            pages_per_group=500,
            workers=8,
            model="ocr_model",
            # Add other parameters as needed
            apply_filter=False,
            markdown=True,  # Enable markdown output
            target_longest_image_dim=1024,
            target_anchor_text_len=6000
        )

        # After processing, upload results to S3
        md_path = f"{workspace}/markdown/*.md"  # Adjust path based on main function output
        # Find the JSONL file with the random string in the output directory

        jsonl_pattern = f"{workspace}/results/output_*.jsonl"
        jsonl_files = glob.glob(jsonl_pattern)
        if jsonl_files:
            json_path = jsonl_files[0]  # Take the first match
        else:
            json_path = None  # Or handle as needed
        
        md_url = f"{root_dir}/{document_id}_olmocr.md"
        json_url = f"{root_dir}/{document_id}_olmocr_content_list.json"

        # Upload results to S3
        if os.path.exists(md_path):
            s3.upload_file_to_s3(md_path, md_url)
        if os.path.exists(json_path):
            s3.upload_file_to_s3(json_path, json_url)

        # Cleanup
        if local_pdf_path and os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)
        
        # Clean up workspace
        
        if os.path.exists(workspace):
            shutil.rmtree(workspace)

        logger.info(f"Successfully processed: {document_id}")
        return md_url, json_url

    except Exception as e:
        error_message = f"Error processing {local_pdf_path or doc_url}: {e}"
        logger.error(error_message)

        # Create a fail.txt in memory
        fail_content = io.BytesIO(error_message.encode('utf-8'))
        fail_path = f"{root_dir}/fail.txt"
        s3.upload_fileobj_to_s3(fail_content, fail_path)

        # Cleanup on error
        if local_pdf_path and os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)

        raise OSError(error_message)
