from pathlib import Path

from privacy_engine import run_pipeline


def main() -> None:
    input_csv = Path("bankdetails.csv")
    output_dir = Path("outputs")

    try:
        generated_files = run_pipeline(input_csv=input_csv, output_dir=output_dir, level="medium")
    except FileNotFoundError as exc:
        print(exc)
        return
    except ValueError as exc:
        print(f"Validation error: {exc}")
        return
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        return

    print("Anonymization completed successfully.")
    for label, file_path in generated_files.items():
        print(f"{label}: {file_path}")


if __name__ == "__main__":
    main()
