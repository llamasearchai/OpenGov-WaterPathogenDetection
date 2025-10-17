"""Command-line interface for OpenGov-WaterPathogenDetection."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .core.config import get_settings
from .core.database import DatabaseManager
from .services.agent_service import AgentService
from .services.ollama_service import OllamaService
from .utils.logging import get_logger

# Initialize console and logger (logging configured lazily on first callback)
console = Console()
logger = get_logger(__name__)

# Create the main Typer app
app = typer.Typer(
    name="openwaterpathogendetection",
    help="OpenGov-WaterPathogenDetection – Comprehensive water pathogen detection program administration system for California public health laboratories supporting pathogen monitoring and outbreak detection",
    add_completion=False,
)

# Sub-apps for organization
agent_app = typer.Typer(help="AI-powered analysis commands")
db_app = typer.Typer(help="Database management commands")
llm_app = typer.Typer(help="LLM and model management commands")
query_app = typer.Typer(help="Data query and analysis commands")
pathogen_app = typer.Typer(help="Pathogen management commands")
sample_app = typer.Typer(help="Water sample collection commands")
export_app = typer.Typer(help="Data export commands")
app.add_typer(agent_app, name="agent")
app.add_typer(db_app, name="db")
app.add_typer(llm_app, name="llm")
app.add_typer(query_app, name="query")
app.add_typer(pathogen_app, name="pathogen")
app.add_typer(sample_app, name="sample")
app.add_typer(export_app, name="export")


@app.callback()
def callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Global options (invoked before any subcommand)."""
    from .utils.logging import configure_logging
    if config:
        os.environ["OPENWATERPATHOGENDETECTION_CONFIG"] = str(config)
    # Configure logging once here (idempotent if already configured)
    configure_logging(debug=verbose or get_settings().debug)
    if verbose:
        logger.debug("Verbose logging enabled", verbose=verbose)


# Removed early simplistic menu; a richer interactive system can be reintroduced later.


@agent_app.command("run")
def agent_run(
    prompt: str = typer.Argument(..., help="Analysis prompt for the AI agent"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="Model to use for analysis"),
    provider: str = typer.Option("openai", "--provider", "-p", help="AI provider (openai/ollama)"),
):
    """Run AI-powered analysis."""
    console.print(f"[bold green]Running Analysis[/bold green]")
    console.print(f"Prompt: {prompt}")
    console.print(f"Model: {model}")
    console.print(f"Provider: {provider}")
    console.print("-" * 50)

    from .utils.logging import configure_logging
    configure_logging(debug=get_settings().debug)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing...", total=None)

        try:
            settings = get_settings()
            agent_service = AgentService()
            result = asyncio.run(agent_service.run_analysis(prompt, model, provider))

            progress.update(task, completed=True)
            console.print("[bold green]Analysis Complete[/bold green]")
            console.print(f"Result: {result}")

        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]Analysis Failed: {e}[/bold red]")
            raise typer.Exit(1)


@db_app.command("init")
def db_init(
    drop_existing: bool = typer.Option(False, "--drop-existing", help="Drop existing database"),
):
    """Initialize the database."""
    console.print("[bold blue]Initializing Database[/bold blue]")

    from .utils.logging import configure_logging
    configure_logging(debug=get_settings().debug)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up database...", total=None)

        try:
            db_manager = DatabaseManager()
            db_manager.initialize(drop_existing=drop_existing)
            progress.update(task, completed=True)
            console.print("[bold green]Database initialized[/bold green]")

        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]Failed: {e}[/bold red]")
            raise typer.Exit(1)


@db_app.command("seed")
def db_seed():
    """Seed database with sample data."""
    console.print("[bold blue]Seeding Database[/bold blue]")

    from .utils.logging import configure_logging
    configure_logging(debug=get_settings().debug)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Seeding database...", total=None)

        try:
            db_manager = DatabaseManager()
            db_manager.seed_sample_data()
            progress.update(task, completed=True)
            console.print("[bold green]Database seeded[/bold green]")

        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]Failed: {e}[/bold red]")
            raise typer.Exit(1)


@app.command("serve-datasette")
def serve_datasette(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8001, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Serve the Datasette web interface."""
    console.print("[bold blue]Starting Dashboard[/bold blue]")
    console.print(f"Host: {host}")
    console.print(f"Port: {port}")

    from .utils.logging import configure_logging
    configure_logging(debug=get_settings().debug)

    try:
        import subprocess
        settings = get_settings()
        db_path = Path("data/opengovwaterpathogendetection.db")
        cmd = [sys.executable, "-m", "datasette", str(db_path), "--host", host, "--port", str(port)]

        if reload:
            cmd.append("--reload")

        console.print("[bold green]Dashboard starting...[/bold green]")
        console.print(f"Open http://{host}:{port} in your browser")
        subprocess.run(cmd)

    except Exception as e:
        console.print(f"[bold red]Failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def root_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Top-level callback providing global options."""
    from .utils.logging import configure_logging
    settings = get_settings()
    configure_logging(debug=verbose or settings.debug)
    if version:
        console.print(f"[bold blue]{settings.app_name} v{settings.version}[/bold blue]")
        raise typer.Exit(0)
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    if config:
        os.environ["OPENWATERPATHOGENDETECTION_CONFIG"] = str(config)
    if ctx.invoked_subcommand is None:
        console.print(f"[bold green]{settings.app_name} CLI - use --help for commands" )

@app.command("init")
def init_command(
    drop_existing: bool = typer.Option(False, "--drop-existing", help="Drop existing database first"),
):
    """Initialize the application database (alias for db init)."""
    from .utils.logging import configure_logging
    configure_logging(debug=get_settings().debug)
    db_manager = DatabaseManager()
    db_manager.initialize(drop_existing=drop_existing)
    console.print("[bold green]Database initialized[/bold green]")


@app.command("serve")
def serve_api(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to."),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to."),
):
    """
    Start FastAPI web server for API access.
    """
    console.print(f"Starting FastAPI server on {host}:{port}...")
    console.print(f"[bold green]Open your browser to: http://{host}:{port}[/bold green]")
    console.print(f"[bold blue]API Documentation: http://{host}:{port}/docs[/bold blue]")

    from .utils.logging import configure_logging
    configure_logging(debug=get_settings().debug)

    try:
        import uvicorn
        uvicorn.run(
            "opengovwaterpathogendetection.web.app:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        console.print("\n[bold blue]FastAPI server stopped.[/bold blue]")
    except Exception as e:
        console.print(f"[bold red]Error starting FastAPI server: {e}[/bold red]")
        raise typer.Exit(1)





"""Legacy interactive menu system removed.

Rationale:
- The previous implementation referenced undefined symbols (repo_name, export_submenu, status_submenu, init_db,
  db_commands, run_agent) causing Pylance reportUndefinedVariable diagnostics.
- This functionality overlapped with explicit Typer subcommands already provided (db init, db seed, serve, etc.).
- To keep the CLI surface area focused and type-safe, the interactive text menu has been removed. If an
  interactive TUI is desired in the future, it can be reintroduced in a dedicated module with full test coverage.
"""

# NOTE: If needed later, a lightweight placeholder command can be re-added.
# Example:
# @app.command("menu")
# def menu_placeholder():
#     """Placeholder for future interactive menu."""
#     console.print("Interactive menu has been removed. Use --help to see available commands.")


@app.command("export")
def export_data(
    format: str = typer.Option("json", "--format", "-f", help="Export format (json/csv)"),
    output_dir: str = typer.Option("exports", "--output", "-o", help="Output directory"),
):
    """Export pathogen detection data."""
    console.print(f"[bold blue]Exporting Data[/bold blue]")
    
    try:
        from .utils.export import DataExporter
        from .storage.pathogen_storage import PathogenStorage
        
        exporter = DataExporter(output_dir)
        storage = PathogenStorage()
        
        pathogens = storage.list_pathogens(limit=1000)
        data = [p.__dict__ for p in pathogens if hasattr(p, '__dict__')]
        
        if format == "csv":
            filepath = exporter.export_to_csv(data)
        else:
            filepath = exporter.export_to_json(data)
        
        console.print(f"[bold green]Data exported to: {filepath}[/bold green]")
        storage.close()
    except Exception as e:
        console.print(f"[bold red]Export failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("risk-assess")
def risk_assessment(
    pathogen_type: str = typer.Argument(..., help="Pathogen type"),
    concentration: float = typer.Argument(..., help="Concentration (CFU/100mL)"),
    location: str = typer.Argument(..., help="Sample location"),
    population: int = typer.Option(None, "--population", "-p", help="Population exposed"),
):
    """Perform risk assessment for pathogen detection."""
    console.print(f"[bold blue]Risk Assessment[/bold blue]")
    
    try:
        from .services.risk_assessment import RiskAssessmentService, RiskLevel
        from .models.pathogen import PathogenType
        
        service = RiskAssessmentService()
        pathogen_type_enum = PathogenType(pathogen_type.lower())
        
        assessment = service.assess_risk(
            pathogen_type=pathogen_type_enum,
            concentration=concentration,
            location=location,
            population_exposed=population
        )
        
        console.print(f"\n[bold]Risk Level:[/bold] {assessment['risk_level'].upper()}")
        console.print(f"[bold]Location:[/bold] {assessment['location']}")
        console.print(f"[bold]Concentration:[/bold] {assessment['concentration']} CFU/100mL")
        
        if assessment.get('requires_action'):
            console.print("\n[bold red]IMMEDIATE ACTION REQUIRED[/bold red]")
        
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in assessment['recommendations']:
            console.print(f"  - {rec}")
        
    except Exception as e:
        console.print(f"[bold red]Assessment failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("status")
def status_command(json_output: bool = typer.Option(False, "--json", help="Output status as JSON")):
    """Show current configuration, database path, and environment info.

    Use --json for machine-readable output.
    """
    import json as _json
    settings = get_settings()
    from .utils.logging import configure_logging
    configure_logging(debug=settings.debug)

    db_path = settings.database_url.replace("sqlite:///", "")
    payload = {
        "app_name": settings.app_name,
        "version": settings.version,
        "debug": settings.debug,
        "database": db_path,
        "openai_key_set": bool(settings.openai_api_key),
        "ollama_base_url": settings.ollama_base_url,
        "log_level": settings.log_level,
        "structured_logging": settings.structured_logging,
    }

    if json_output:
        console.print(_json.dumps(payload, indent=2))
    else:
        table = Table(title="OpenGov-WaterPathogenDetection Status", show_header=True, header_style="bold magenta")
        table.add_column("Key")
        table.add_column("Value")
        for k, v in payload.items():
            table.add_row(k.replace("_", " ").title(), str(v))
        console.print(table)

    logger.info("Status displayed", **payload)


@pathogen_app.command("list")
def pathogen_list(
    pathogen_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type (bacteria/virus/parasite)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to show"),
):
    """List all pathogens in the database."""
    from .storage.pathogen_storage import PathogenStorage
    from .utils.logging import configure_logging

    configure_logging(debug=get_settings().debug)
    storage = PathogenStorage()

    try:
        from .models.pathogen import PathogenType
        pt = PathogenType(pathogen_type) if pathogen_type else None
        pathogens = storage.list_pathogens(limit=limit, pathogen_type=pt)

        if not pathogens:
            console.print("[yellow]No pathogens found[/yellow]")
            return

        table = Table(title=f"Waterborne Pathogens ({len(pathogens)} records)", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Common Name", style="yellow")
        table.add_column("Incubation (days)", justify="right")

        for p in pathogens:
            table.add_row(
                p.name,
                p.pathogen_type.value if hasattr(p.pathogen_type, 'value') else str(p.pathogen_type),
                p.common_name or "N/A",
                str(p.incubation_period_days) if p.incubation_period_days else "N/A"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        storage.close()


@pathogen_app.command("info")
def pathogen_info(
    name: str = typer.Argument(..., help="Pathogen name or partial name to search")
):
    """Show detailed information about a pathogen."""
    from .storage.pathogen_storage import PathogenStorage
    from .utils.logging import configure_logging

    configure_logging(debug=get_settings().debug)
    storage = PathogenStorage()

    try:
        results = storage.search_pathogens(name)

        if not results:
            console.print(f"[yellow]No pathogen found matching '{name}'[/yellow]")
            raise typer.Exit(0)

        pathogen = results[0]

        console.print(f"\n[bold cyan]{pathogen.name}[/bold cyan]")
        console.print(f"[bold]Common Name:[/bold] {pathogen.common_name or 'N/A'}")
        console.print(f"[bold]Type:[/bold] {pathogen.pathogen_type.value if hasattr(pathogen.pathogen_type, 'value') else str(pathogen.pathogen_type)}")
        console.print(f"\n[bold]Description:[/bold]\n{pathogen.description or 'N/A'}")
        console.print(f"\n[bold]Symptoms:[/bold]\n{pathogen.symptoms or 'N/A'}")
        console.print(f"\n[bold]Transmission:[/bold] {pathogen.transmission_route or 'N/A'}")
        console.print(f"[bold]Incubation Period:[/bold] {pathogen.incubation_period_days} days" if pathogen.incubation_period_days else "[bold]Incubation Period:[/bold] Unknown")
        console.print(f"[bold]Infectious Dose:[/bold] {pathogen.infectious_dose or 'Unknown'}")

        if len(results) > 1:
            console.print(f"\n[dim]Found {len(results)} matches. Showing first result.[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        storage.close()


@pathogen_app.command("stats")
def pathogen_stats():
    """Show pathogen database statistics."""
    from .storage.pathogen_storage import PathogenStorage
    from .utils.logging import configure_logging

    configure_logging(debug=get_settings().debug)
    storage = PathogenStorage()

    try:
        stats = storage.get_pathogen_stats()

        console.print("\n[bold cyan]Pathogen Database Statistics[/bold cyan]")
        console.print(f"[bold]Total Pathogens:[/bold] {stats['total_pathogens']}")

        console.print("\n[bold]By Type:[/bold]")
        for ptype, count in stats['by_type'].items():
            console.print(f"  {ptype}: {count}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        storage.close()

@sample_app.command("collect")
def sample_collect(
    location: str = typer.Option(..., "--location", "-l", help="Sample collection location"),
    source_type: str = typer.Option(..., "--source", "-s", help="Source type (drinking_water/wastewater/surface_water)"),
    latitude: Optional[float] = typer.Option(None, "--lat", help="GPS latitude"),
    longitude: Optional[float] = typer.Option(None, "--lon", help="GPS longitude"),
    temperature: Optional[float] = typer.Option(None, "--temp", "-t", help="Water temperature in Celsius"),
    ph: Optional[float] = typer.Option(None, "--ph", help="pH level"),
    turbidity: Optional[float] = typer.Option(None, "--turbidity", help="Turbidity in NTU"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Additional notes"),
):
    """Collect and record a new water sample."""
    from .storage.water_sample_storage import WaterSampleStorage
    from .models.pathogen import WaterSampleCreate, SampleSource
    from .utils.logging import configure_logging
    from datetime import datetime, timezone

    configure_logging(debug=get_settings().debug)
    storage = WaterSampleStorage()

    try:
        sample = WaterSampleCreate(
            location=location,
            source_type=SampleSource(source_type),
            collection_date=datetime.now(timezone.utc),
            latitude=latitude,
            longitude=longitude,
            temperature_celsius=temperature,
            ph_level=ph,
            turbidity_ntu=turbidity,
            notes=notes
        )

        created = storage.create_sample(sample)

        console.print(f"\n[bold green]Sample Collected Successfully![/bold green]")
        console.print(f"Sample ID: {created.id}")
        console.print(f"Location: {created.location}")
        console.print(f"Source: {created.source_type.value}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        storage.close()


@sample_app.command("list")
def sample_list(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of samples to show"),
    source_type: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source type"),
):
    """List water samples."""
    from .storage.water_sample_storage import WaterSampleStorage
    from .models.pathogen import SampleSource
    from .utils.logging import configure_logging
    from datetime import datetime

    configure_logging(debug=get_settings().debug)
    storage = WaterSampleStorage()

    try:
        st = SampleSource(source_type) if source_type else None
        samples = storage.list_samples(limit=limit, source_type=st)

        if not samples:
            console.print("[yellow]No samples found[/yellow]")
            return

        table = Table(title=f"Water Samples ({len(samples)} records)", show_header=True, header_style="bold cyan")
        table.add_column("Location", style="green")
        table.add_column("Source", style="blue")
        table.add_column("Temp (°C)", justify="right")
        table.add_column("pH", justify="right")

        for s in samples:
            table.add_row(
                s.location[:30],
                s.source_type.value if hasattr(s.source_type, 'value') else str(s.source_type),
                f"{s.temperature_celsius:.1f}" if s.temperature_celsius else "N/A",
                f"{s.ph_level:.1f}" if s.ph_level else "N/A"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        storage.close()


@sample_app.command("stats")
def sample_stats():
    """Show water sample statistics."""
    from .storage.water_sample_storage import WaterSampleStorage
    from .utils.logging import configure_logging

    configure_logging(debug=get_settings().debug)
    storage = WaterSampleStorage()

    try:
        stats = storage.get_sample_stats()

        console.print("\n[bold cyan]Water Sample Statistics[/bold cyan]")
        console.print(f"[bold]Total Samples:[/bold] {stats['total_samples']}")

        if stats['by_source_type']:
            console.print("\n[bold]By Source Type:[/bold]")
            for source, count in stats['by_source_type'].items():
                console.print(f"  {source}: {count}")

        if stats['average_temperature_celsius']:
            console.print(f"\n[bold]Average Temperature:[/bold] {stats['average_temperature_celsius']}°C")
        if stats['average_ph_level']:
            console.print(f"[bold]Average pH:[/bold] {stats['average_ph_level']}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        storage.close()


@export_app.command("pathogens")
def export_pathogens(
    output: str = typer.Option(..., "--output", "-o", help="Output file path"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json/csv)"),
    pathogen_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type"),
):
    """Export pathogen data to JSON or CSV."""
    from .utils.export import DataExporter
    from .models.pathogen import PathogenType
    from .utils.logging import configure_logging

    configure_logging(debug=get_settings().debug)
    exporter = DataExporter()

    try:
        pt = PathogenType(pathogen_type) if pathogen_type else None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Exporting pathogens...", total=None)

            if format.lower() == "json":
                count = exporter.export_pathogens_to_json(output, pt)
            elif format.lower() == "csv":
                count = exporter.export_pathogens_to_csv(output, pt)
            else:
                console.print(f"[bold red]Invalid format: {format}. Use 'json' or 'csv'[/bold red]")
                raise typer.Exit(1)

            progress.update(task, completed=True)

        console.print(f"[bold green]Exported {count} pathogens to {output}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Export failed: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        exporter.close()


@export_app.command("samples")
def export_samples(
    output: str = typer.Option(..., "--output", "-o", help="Output file path"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json/csv)"),
    source_type: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source type"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by location"),
):
    """Export water sample data to JSON or CSV."""
    from .utils.export import DataExporter
    from .models.pathogen import SampleSource
    from .utils.logging import configure_logging

    configure_logging(debug=get_settings().debug)
    exporter = DataExporter()

    try:
        st = SampleSource(source_type) if source_type else None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Exporting water samples...", total=None)

            if format.lower() == "json":
                count = exporter.export_water_samples_to_json(output, st, location)
            elif format.lower() == "csv":
                count = exporter.export_water_samples_to_csv(output, st, location)
            else:
                console.print(f"[bold red]Invalid format: {format}. Use 'json' or 'csv'[/bold red]")
                raise typer.Exit(1)

            progress.update(task, completed=True)

        console.print(f"[bold green]Exported {count} water samples to {output}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Export failed: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        exporter.close()


@export_app.command("all")
def export_all(
    output_dir: str = typer.Option("exports", "--output", "-o", help="Output directory"),
):
    """Export all data (pathogens and water samples) to JSON and CSV files."""
    from .utils.export import DataExporter
    from .utils.logging import configure_logging

    configure_logging(debug=get_settings().debug)
    exporter = DataExporter()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Exporting full database...", total=None)

            result = exporter.export_full_database(output_dir)

            progress.update(task, completed=True)

        console.print(f"\n[bold green]Full database exported successfully![/bold green]")
        console.print(f"Output directory: {result['output_directory']}")
        console.print(f"Pathogens exported: {result['pathogens_exported']}")
        console.print(f"Water samples exported: {result['water_samples_exported']}")
        console.print(f"\nFiles created:")
        for file in result['files_created']:
            console.print(f"  - {file}")

    except Exception as e:
        console.print(f"[bold red]Export failed: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        exporter.close()
