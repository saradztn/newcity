#!/usr/bin/env python3
"""
run_pipeline.py - Master Pipeline Execution Script
Runs procedural generation and automatically validates all generated assets.
Usage:
    python3 run_pipeline.py [--clean] [--seed 42] [--full-city]
"""

import sys
import argparse
from city.generator.city import CityOrchestrator
from city.generator.validator import ProjectValidator


def main():
    parser = argparse.ArgumentParser(description="New American City - Procedural Build Pipeline")
    parser.add_argument("--clean", action="store_true", default=True, help="Clean existing generated files before building")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed")
    parser.add_argument("--full-city", action="store_true", help="Generate full metropolis instead of vertical slice")
    parser.add_argument("--resource-dir", type=str, default="resource", help="Target MTA:SA resource directory")
    args = parser.parse_args()

    print("\n=======================================================")
    print("🏙️  NEW AMERICAN CITY - GRAPHICS ENGINE & ASSET PIPELINE")
    print("=======================================================\n")

    orchestrator = CityOrchestrator(
        resource_dir=args.resource_dir,
        seed=args.seed,
        is_vertical_slice=not args.full_city
    )

    if args.clean:
        print("Cleaning previous build artifacts...")
        orchestrator.clean()

    # Step 1: Procedural Asset Generation
    orchestrator.generate_all()

    # Step 2: Quality & Structural Validation
    print("\nRunning comprehensive validation suite...")
    validator = ProjectValidator(resource_dir=args.resource_dir)
    success = validator.run_all()

    if not success:
        print("\n❌ Pipeline completed with ERRORS! Review log above.\n")
        sys.exit(1)
    else:
        print("\n✅ PIPELINE BUILD & VALIDATION COMPLETED SUCCESSFULLY!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
