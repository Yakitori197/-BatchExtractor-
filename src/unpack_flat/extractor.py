"""
Main extractor module - recursively extracts archives and flattens output.
"""

import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TaskID, TextColumn
from rich.table import Table

from .config import DEFAULT_MAX_ROUNDS, DEFAULT_WORKERS, is_archive
from .manifest import ManifestWriter
from .resolver import FilenameResolver
from .sevenzip import SevenZipNotFoundError, check_7z_available, extract_archive


@dataclass
class ExtractionStats:
    """Statistics about the extraction process."""
    scanned_files: int = 0
    archives_found: int = 0
    archives_extracted: int = 0
    files_output: int = 0
    files_renamed: int = 0
    files_skipped: int = 0
    errors: int = 0
    rounds_completed: int = 0
    total_size_bytes: int = 0
    error_messages: list = field(default_factory=list)


class UnpackFlat:
    """
    Recursively extracts nested archives and flattens all files to a single output directory.
    """

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        max_rounds: int = DEFAULT_MAX_ROUNDS,
        keep_archives: bool = False,
        dry_run: bool = False,
        workers: int = DEFAULT_WORKERS,
        compute_hash: bool = True,
        manifest_format: Literal["jsonl", "csv"] = "jsonl",
        password: Optional[str] = None,
        console: Optional[Console] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ):
        """
        Initialize the extractor.
        
        Args:
            input_dir: Directory containing files/archives to process
            output_dir: Directory to output flattened files
            max_rounds: Maximum extraction rounds (prevents infinite loops)
            keep_archives: Whether to keep archives after extraction
            dry_run: If True, only report what would be done
            workers: Number of parallel workers
            compute_hash: Whether to compute SHA256 for manifest
            manifest_format: Format for manifest file ('jsonl' or 'csv')
            password: Optional password for encrypted archives
            progress_callback: Optional callback for progress updates
        """
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.max_rounds = max_rounds
        self.keep_archives = keep_archives
        self.dry_run = dry_run
        self.workers = workers
        self.compute_hash = compute_hash
        self.manifest_format = manifest_format
        self.password = password
        self.progress_callback = progress_callback

        self.console = console or Console()
        self.stats = ExtractionStats()

        # Working directory for extraction
        self._work_dir: Optional[Path] = None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None

        # Track processed archives to avoid re-processing
        self._processed_archives: set[str] = set()

        # Distinct files seen while scanning. Each round re-walks the work dir,
        # so a plain counter would count the same file once per round (and the
        # summary would report far more files than actually exist).
        self._scanned_paths: set[Path] = set()

    @property
    def work_dir(self) -> Path:
        """
        Working directory, guaranteed non-None.

        _work_dir is Optional until _setup_work_dir() runs; callers used it as a
        plain Path, which the type checker rightly rejected and which would fail
        at runtime if the setup step were ever skipped.
        """
        if self._work_dir is None:
            raise RuntimeError("Working directory is not set up yet")
        return self._work_dir

    def _check_prerequisites(self) -> bool:
        """Check that 7-Zip is available."""
        available, message = check_7z_available()
        if not available:
            self.console.print(f"[red]Error:[/red] {message}")
            return False
        self.console.print(f"[green]✓[/green] {message}")
        return True

    def _setup_directories(self) -> None:
        """Set up working and output directories."""
        # Create output directory
        if not self.dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary working directory
        if not self.dry_run:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="unpack_flat_")
            self._work_dir = Path(self._temp_dir.name)

            # Copy input to working directory
            self.console.print("[dim]Copying input to working directory...[/dim]")
            shutil.copytree(self.input_dir, self._work_dir / "input", dirs_exist_ok=True)
            self._work_dir = self._work_dir / "input"
        else:
            self._work_dir = self.input_dir

    def _cleanup(self) -> None:
        """Clean up temporary directories."""
        if self._temp_dir:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass

    def _scan_for_archives(self, directory: Path) -> list[Path]:
        """
        Scan directory recursively for archive files.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of archive file paths
        """
        archives = []

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                # Count distinct files, not walk hits: this dir is re-scanned
                # every round, so incrementing a counter would inflate the total.
                self._scanned_paths.add(file_path.resolve())

                if is_archive(file_path):
                    # Skip already processed archives
                    archive_id = f"{file_path.name}_{file_path.stat().st_size}"
                    if archive_id not in self._processed_archives:
                        archives.append(file_path)

        self.stats.scanned_files = len(self._scanned_paths)
        return archives

    def _scan_for_regular_files(self, directory: Path) -> list[Path]:
        """
        Scan directory recursively for non-archive files.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of regular file paths
        """
        files = []

        for root, _, filenames in os.walk(directory):
            for file in filenames:
                file_path = Path(root) / file
                if not is_archive(file_path):
                    files.append(file_path)

        return files

    def _extract_single_archive(
        self,
        archive_path: Path,
        extract_to: Path
    ) -> tuple[bool, str, list[Path]]:
        """
        Extract a single archive.
        
        Args:
            archive_path: Path to the archive
            extract_to: Directory to extract to
            
        Returns:
            Tuple of (success, message, list_of_extracted_files)
        """
        if self.dry_run:
            return True, "Dry run - would extract", []

        extract_to.mkdir(parents=True, exist_ok=True)

        success, message = extract_archive(
            archive_path,
            extract_to,
            password=self.password
        )

        if success:
            # Mark as processed
            archive_id = f"{archive_path.name}_{archive_path.stat().st_size if archive_path.exists() else 0}"
            self._processed_archives.add(archive_id)

            # List extracted files
            extracted = list(extract_to.rglob("*"))
            extracted = [f for f in extracted if f.is_file()]

            return True, message, extracted

        return False, message, []

    def _run_extraction_round(
        self,
        round_num: int,
        archives: list[Path],
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> int:
        """
        Run a single round of archive extraction.

        Args:
            round_num: Current round number
            archives: Archives found by the caller's scan. Passed in rather than
                re-scanned here: run() already scanned this round, and scanning
                again walked the whole tree a second time per round.
            progress: Optional Rich progress bar
            task_id: Optional task ID for progress bar

        Returns:
            Number of archives extracted this round
        """
        self.stats.archives_found += len(archives)

        if not archives:
            return 0

        extracted_count = 0

        if self.dry_run:
            for archive in archives:
                self.console.print(f"  [dim]Would extract:[/dim] {archive.name}")
                # Mark as processed to avoid re-scanning in dry-run
                archive_id = f"{archive.name}_{archive.stat().st_size if archive.exists() else 0}"
                self._processed_archives.add(archive_id)
                extracted_count += 1
            return extracted_count

        # Extract archives (optionally in parallel)
        def extract_one(archive: Path) -> tuple[Path, bool, str]:
            extract_subdir = self.work_dir / f"_extracted_{archive.stem}_{id(archive)}"
            success, message, _ = self._extract_single_archive(archive, extract_subdir)
            return archive, success, message

        if self.workers > 1 and len(archives) > 1:
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {executor.submit(extract_one, a): a for a in archives}

                for future in as_completed(futures):
                    archive, success, message = future.result()
                    if progress and task_id:
                        progress.advance(task_id)

                    if success:
                        extracted_count += 1
                        self.stats.archives_extracted += 1

                        # Delete archive if not keeping
                        if not self.keep_archives and archive.exists():
                            try:
                                archive.unlink()
                            except Exception:
                                pass
                    else:
                        self.stats.errors += 1
                        self.stats.error_messages.append(f"{archive.name}: {message}")
        else:
            for archive in archives:
                archive, success, message = extract_one(archive)
                if progress and task_id:
                    progress.advance(task_id)

                if success:
                    extracted_count += 1
                    self.stats.archives_extracted += 1

                    if not self.keep_archives and archive.exists():
                        try:
                            archive.unlink()
                        except Exception:
                            pass
                else:
                    self.stats.errors += 1
                    self.stats.error_messages.append(f"{archive.name}: {message}")

        return extracted_count

    def _flatten_files(
        self,
        manifest_writer: Optional[ManifestWriter],
        resolver: FilenameResolver,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> None:
        """
        Flatten all regular files to the output directory.
        
        Args:
            manifest_writer: Optional manifest writer
            resolver: Filename resolver for conflicts
            progress: Optional Rich progress bar
            task_id: Optional task ID for progress bar
        """
        files = self._scan_for_regular_files(self.work_dir)

        for file_path in files:
            if progress and task_id:
                progress.advance(task_id)

            original_name = file_path.name
            relative_source = file_path.relative_to(self.work_dir)

            if self.dry_run:
                would_conflict = resolver.check_conflict(original_name)
                status = "[yellow]→ rename[/yellow]" if would_conflict else "[green]→ copy[/green]"
                self.console.print(f"  {status} {original_name}")
                if would_conflict:
                    resolver.reserve_name(f"_reserved_{id(file_path)}")
                else:
                    resolver.reserve_name(original_name)
                self.stats.files_output += 1
                continue

            # Resolve filename and get output path
            output_path, final_name, was_renamed = resolver.get_output_path(
                original_name,
                source_path=file_path
            )

            try:
                # Copy file to output
                shutil.copy2(file_path, output_path)
                self.stats.files_output += 1
                self.stats.total_size_bytes += output_path.stat().st_size

                if was_renamed:
                    self.stats.files_renamed += 1

                # Write manifest entry
                if manifest_writer:
                    manifest_writer.add_entry(
                        source_path=relative_source,
                        output_path=output_path,
                        renamed=was_renamed,
                        original_filename=original_name,
                        archive_source=str(relative_source.parent) if relative_source.parent != Path(".") else ""
                    )

            except Exception as e:
                self.stats.errors += 1
                self.stats.error_messages.append(f"Failed to copy {original_name}: {e}")

    def run(self) -> ExtractionStats:
        """
        Run the extraction process.
        
        Returns:
            ExtractionStats with details about the operation
        """
        self.console.print()
        self.console.print("[bold]═══ unpack-flat ═══[/bold]")
        self.console.print()

        # Check prerequisites
        if not self._check_prerequisites():
            raise SevenZipNotFoundError("7-Zip is required but not found")

        self.console.print()
        self.console.print(f"[bold]Input:[/bold]  {self.input_dir}")
        self.console.print(f"[bold]Output:[/bold] {self.output_dir}")
        self.console.print(f"[bold]Mode:[/bold]   {'DRY RUN' if self.dry_run else 'Live'}")
        self.console.print()

        try:
            # Setup
            self._setup_directories()
            resolver = FilenameResolver(self.output_dir)

            # Open manifest writer
            manifest_path = self.output_dir / f"manifest.{self.manifest_format}"
            manifest_writer = None

            if not self.dry_run:
                manifest_writer = ManifestWriter(
                    manifest_path,
                    format=self.manifest_format,
                    compute_hash=self.compute_hash
                )
                manifest_writer.__enter__()

            try:
                # Extraction rounds
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    MofNCompleteColumn(),
                    console=self.console
                ) as progress:

                    for round_num in range(1, self.max_rounds + 1):
                        self.console.print(f"\n[bold]Round {round_num}[/bold]")

                        # Scan for archives
                        archives = self._scan_for_archives(self.work_dir)

                        if not archives:
                            self.console.print("  [dim]No archives found - extraction complete[/dim]")
                            break

                        self.console.print(f"  Found {len(archives)} archive(s)")

                        # Extract archives
                        task = progress.add_task(
                            f"  Extracting round {round_num}",
                            total=len(archives)
                        )

                        extracted = self._run_extraction_round(round_num, archives, progress, task)
                        self.stats.rounds_completed = round_num

                        progress.remove_task(task)

                        if extracted == 0:
                            break

                        self.console.print(f"  [green]✓[/green] Extracted {extracted} archive(s)")

                    else:
                        self.console.print(
                            f"\n[yellow]Warning:[/yellow] Reached max rounds ({self.max_rounds}). "
                            "Some archives may remain."
                        )

                    # Flatten files
                    self.console.print("\n[bold]Flattening files to output...[/bold]")

                    files = self._scan_for_regular_files(self.work_dir)
                    task = progress.add_task("  Copying files", total=len(files))

                    self._flatten_files(manifest_writer, resolver, progress, task)

                    progress.remove_task(task)

            finally:
                if manifest_writer:
                    manifest_writer.__exit__(None, None, None)

            # Print summary
            self._print_summary()

            return self.stats

        finally:
            self._cleanup()

    def _print_summary(self) -> None:
        """Print a summary of the extraction process."""
        self.console.print()
        self.console.print("[bold]═══ Summary ═══[/bold]")
        self.console.print()

        table = Table(show_header=False, box=None)
        table.add_column(style="dim")
        table.add_column()

        table.add_row("Files scanned:", str(self.stats.scanned_files))
        table.add_row("Archives found:", str(self.stats.archives_found))
        table.add_row("Archives extracted:", str(self.stats.archives_extracted))
        table.add_row("Extraction rounds:", str(self.stats.rounds_completed))
        table.add_row("Files output:", str(self.stats.files_output))
        table.add_row("Files renamed:", str(self.stats.files_renamed))
        table.add_row("Errors:", str(self.stats.errors))

        if self.stats.total_size_bytes > 0:
            size_mb = self.stats.total_size_bytes / (1024 * 1024)
            table.add_row("Total size:", f"{size_mb:.2f} MB")

        self.console.print(table)

        if self.stats.error_messages:
            self.console.print()
            self.console.print("[red]Errors:[/red]")
            for msg in self.stats.error_messages[:10]:  # Show first 10
                self.console.print(f"  • {msg}")
            if len(self.stats.error_messages) > 10:
                self.console.print(f"  ... and {len(self.stats.error_messages) - 10} more")

        if not self.dry_run:
            self.console.print()
            self.console.print(f"[green]✓[/green] Output written to: {self.output_dir}")
            manifest_file = self.output_dir / f"manifest.{self.manifest_format}"
            if manifest_file.exists():
                self.console.print(f"[green]✓[/green] Manifest written to: {manifest_file}")
