import asyncio
import os
import logging
from temporalio.client import Client
from workflows import ConfidentialWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "confidential-workflow-poc")
TASK_QUEUE = os.environ.get("TASK_QUEUE", "confidential-workflow-tasks")

async def main():
    logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}")
    client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
    
    logger.info("Starting workflow...")
    input_payload = "Sensitive Data Needs Encryption"
    
    handle = await client.start_workflow(
        ConfidentialWorkflow.run,
        input_payload,
        id="confidential-workflow-test-1",
        task_queue=TASK_QUEUE,
    )

    logger.info(f"Workflow started. ID: {handle.id}, RunID: {handle.run_id}")
    logger.info("Waiting for result...")
    
    result = await handle.result()
    logger.info(f"Workflow Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
