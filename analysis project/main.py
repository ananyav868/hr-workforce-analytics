"""Main entry-point script for the HR Workforce Analytics pipeline.

Parses CLI arguments, instantiates the PipelineOrchestrator, and runs
the end-to-end pipeline. Exits with code 0 on success, 1 on failure.

Requirements: 10.1, 10.3
"""

import argparse
import logging
import sys

from src.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)


def _configure_root_logging() -> None:
    """Configure basic root logging for early startup messages.

    The PipelineOrchestrator will add file and console handlers with
    structured formatting once it loads the config. This ensures any
    errors during orchestrator initialization are still visible.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def main() -> int:
    """Parse arguments, run the pipeline, and return the exit code."""
    parser = argparse.ArgumentParser(
        description="HR Workforce Analytics & Attrition Prediction Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/pipeline_config.yaml",
        help="Path to the pipeline configuration YAML file (default: config/pipeline_config.yaml)",
    )
    args = parser.parse_args()

    # Set up basic logging so early errors are visible
    _configure_root_logging()

    try:
        orchestrator = PipelineOrchestrator(args.config)
        result = orchestrator.run()

        if result.final_status == "success":
            logger.info("Pipeline finished successfully. Exiting with code 0.")
            return 0
        else:
            logger.error("Pipeline finished with failure. Exiting with code 1.")
            return 1

    except Exception as e:
        logger.error("Unexpected error during pipeline execution: %s", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
