from fastapi import FastAPI, Body, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import uvicorn
import asyncio
from extract import process_disclosure 
app = FastAPI()

# Import your main function (remove the CLI wrapper)
from main import main

async def process_disclosure_task(doc_url: str, document_id: str, source_system: str):
    try:
        print(f"Started processing {document_id}")
        md_url, json_url = await process_disclosure(doc_url, document_id, source_system)
        print(f"Processed {document_id}: md_url={md_url}, json_url={json_url}")
    except Exception as e:
        print(f"Error processing {document_id}: {e}")
    finally:
        if os.path.exists("lockfile.lock"):
            os.remove("lockfile.lock")


def run_async_task(coro):
    """Helper function to run async tasks in background"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.post("/pdf_ocr_extract")
def pdf_ocr_extract(background_tasks: BackgroundTasks, payload: dict = Body(...)):
    try:
        source_system = payload.get("source_system")
        document_id = payload.get("document_id")
        doc_url = payload.get("doc_url")

        if not all([source_system, document_id, doc_url]):
            raise ValueError("Fields 'source_system', 'document_id', and 'doc_url' are required")

        if not os.path.exists("lockfile.lock"):
            open("lockfile.lock", "w").close()
            # Run the async task in background
            background_tasks.add_task(
                run_async_task, 
                process_disclosure_task(doc_url, document_id, source_system)
            )

            return JSONResponse(
                content={"message": "Processing started", "document_id": document_id},
                status_code=202
            )
        else:
            return JSONResponse(
                content={"error": "API is currently busy processing another job."},
                status_code=429
            )

    except Exception as e:
        return JSONResponse(
            content={"error": f"Invalid request: {e}"},
            status_code=400
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)