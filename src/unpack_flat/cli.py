"""
Command-line interface for unpack-flat.
"""

import sys
from pathlib import Path
from typing import Literal

import click
from rich.console import Console

from . import __version__
from .config import DEFAULT_MAX_ROUNDS, DEFAULT_WORKERS
from .extractor import UnpackFlat
from .sevenzip import SevenZipNotFoundError, check_7z_available

console = Console()


@click.command()
@click.option(
    "-i", "--input",
    "input_dir",
    required=False,  # Made optional to allow --check-7z to work
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Input directory containing files and/or archives to process."
)
@click.option(
    "-o", "--output",
    "output_dir",
    required=False,  # Made optional to allow --check-7z to work
    default=None,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Output directory for flattened files."
)
@click.option(
    "--max-rounds",
    default=DEFAULT_MAX_ROUNDS,
    type=int,
    show_default=True,
    help="Maximum extraction rounds (prevents infinite loops)."
)
@click.option(
    "--keep-archives",
    is_flag=True,
    default=False,
    help="Keep archive files after extraction (default: delete from work area)."
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be done without actually extracting or copying."
)
@click.option(
    "-w", "--workers",
    default=DEFAULT_WORKERS,
    type=int,
    show_default=True,
    help="Number of parallel workers for extraction."
)
@click.option(
    "--no-hash",
    is_flag=True,
    default=False,
    help="Skip SHA256 hash computation in manifest (faster for large files)."
)
@click.option(
    "--manifest-format",
    type=click.Choice(["jsonl", "csv"]),
    default="jsonl",
    show_default=True,
    help="Manifest file format."
)
@click.option(
    "-p", "--password",
    default=None,
    help="Password for encrypted archives."
)
@click.option(
    "--check-7z",
    is_flag=True,
    default=False,
    help="Check if 7-Zip is available and exit."
)
@click.version_option(version=__version__, prog_name="unpack-flat")
def main(
    input_dir: Path,
    output_dir: Path,
    max_rounds: int,
    keep_archives: bool,
    dry_run: bool,
    workers: int,
    no_hash: bool,
    # click.Choice(["jsonl", "csv"]) already constrains this at runtime,
    # so the narrower annotation is accurate and satisfies the type checker.
    manifest_format: Literal["jsonl", "csv"],
    password: str,
    check_7z: bool
) -> None:
    """
    Recursively extract nested archives and flatten all files to a single output directory.
    
    \b
    Examples:
      unpack-flat --input ./downloads --output ./extracted
      unpack-flat -i ./in -o ./out --dry-run
      unpack-flat -i ./in -o ./out --keep-archives --workers 8
      unpack-flat -i ./in -o ./out -p "secret" --no-hash
    """
    # Check 7-Zip availability
    if check_7z:
        available, message = check_7z_available()
        if available:
            console.print(f"[green]✓[/green] {message}")
            sys.exit(0)
        else:
            console.print(f"[red]✗[/red] {message}")
            sys.exit(1)

    # Validate required options for normal operation
    if input_dir is None:
        console.print("[red]Error:[/red] Missing option '-i' / '--input'.")
        sys.exit(2)

    if output_dir is None:
        console.print("[red]Error:[/red] Missing option '-o' / '--output'.")
        sys.exit(2)

    # Validate input
    if not input_dir.exists():
        console.print(f"[red]Error:[/red] Input directory does not exist: {input_dir}")
        sys.exit(1)

    if not input_dir.is_dir():
        console.print(f"[red]Error:[/red] Input path is not a directory: {input_dir}")
        sys.exit(1)

    # Check that output is not inside input
    try:
        output_dir.resolve().relative_to(input_dir.resolve())
        console.print("[red]Error:[/red] Output directory cannot be inside input directory.")
        sys.exit(1)
    except ValueError:
        pass  # Good - output is not inside input

    # Check that input is not inside output
    try:
        input_dir.resolve().relative_to(output_dir.resolve())
        console.print("[red]Error:[/red] Input directory cannot be inside output directory.")
        sys.exit(1)
    except ValueError:
        pass  # Good - input is not inside output

    # Validate workers
    if workers < 1:
        console.print("[red]Error:[/red] Workers must be at least 1.")
        sys.exit(1)

    if workers > 32:
        console.print("[yellow]Warning:[/yellow] High worker count may cause I/O contention.")

    # Validate max rounds
    if max_rounds < 1:
        console.print("[red]Error:[/red] Max rounds must be at least 1.")
        sys.exit(1)

    try:
        extractor = UnpackFlat(
            input_dir=input_dir,
            output_dir=output_dir,
            max_rounds=max_rounds,
            keep_archives=keep_archives,
            dry_run=dry_run,
            workers=workers,
            compute_hash=not no_hash,
            manifest_format=manifest_format,
            password=password,
            console=console
        )

        stats = extractor.run()

        # Exit code based on results
        if stats.errors > 0:
            sys.exit(2)  # Partial success
        sys.exit(0)

    except SevenZipNotFoundError:
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        if console.is_terminal:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
