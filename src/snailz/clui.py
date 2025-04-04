"""Command-line interface for snailz."""

import json
from pathlib import Path
import random
import shutil

import click

from .assays import assays_generate
from .database import database_generate
from .mangle import mangle_assays
from .overall import AllData, AllParams
from .persons import persons_generate
from .specimens import specimens_generate
from .surveys import surveys_generate
from .utils import display, fail, report


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """Entry point for command-line interface."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--csvdir", type=click.Path(), help="Path to CSV directory")
@click.option(
    "--params",
    required=True,
    type=click.Path(exists=True),
    help="Path to parameters file",
)
@click.option("--output", type=click.Path(), help="Path to output file")
@click.pass_context
def data(ctx, csvdir, params, output):
    """Generate and save data using provided parameters."""
    verbose = ctx.obj["verbose"] and output is not None
    try:
        with open(params, "r") as reader:
            parameters = AllParams.model_validate(json.load(reader))
            random.seed(parameters.seed)
            surveys = surveys_generate(parameters.survey)
            persons = persons_generate(parameters.person)
            specimens = specimens_generate(parameters.specimen, surveys)
            assays = assays_generate(parameters.assay, persons, specimens)
            data = AllData(
                assays=assays,
                surveys=surveys,
                params=parameters,
                persons=persons,
                specimens=specimens,
            )
            display(output, data)
            report(verbose, f"wrote data file {output}")
            if csvdir is not None:
                csv_dir_path = Path(csvdir)
                _create_csv(csv_dir_path, data)
                database_generate(
                    csv_dir_path / "assays.csv",
                    csv_dir_path / "people.csv",
                    csv_dir_path / "specimens.csv",
                    csv_dir_path / "snailz.db",
                )
                report(verbose, f"wrote CSV to {output}")
    except OSError as exc:
        fail(str(exc))


@cli.command()
@click.option("--output", type=click.Path(), help="Path to output file")
@click.pass_context
def params(ctx, output):
    """Generate and save parameters."""
    verbose = ctx.obj["verbose"] and output is not None
    try:
        params = AllParams()
        display(output, params)
        report(verbose, f"wrote parameter file {output}")
    except OSError as exc:
        fail(str(exc))


def _create_csv(csv_dir, data):
    """Create CSV files from data."""
    if not csv_dir.is_dir():
        raise ValueError(f"{csv_dir} is not a directory")

    with open(csv_dir / "assays.csv", "w") as writer:
        writer.write(data.assays.to_csv())
    assays_dir = csv_dir / "assays"
    if assays_dir.is_dir():
        shutil.rmtree(assays_dir)
    assays_dir.mkdir(exist_ok=True)
    for assay in data.assays.items:
        for which in ["readings", "treatments"]:
            with open(assays_dir / f"{assay.ident}_{which}.csv", "w") as writer:
                writer.write(assay.to_csv(which))

    mangle_assays(csv_dir / "assays", data.persons)

    surveys_dir = csv_dir / "surveys"
    if surveys_dir.is_dir():
        shutil.rmtree(surveys_dir)
    surveys_dir.mkdir(exist_ok=True)
    for survey in data.surveys.items:
        with open(surveys_dir / f"{survey.ident}.csv", "w") as writer:
            writer.write(survey.to_csv())

    with open(csv_dir / "people.csv", "w") as writer:
        writer.write(data.persons.to_csv())

    with open(csv_dir / "specimens.csv", "w") as writer:
        writer.write(data.specimens.to_csv())


if __name__ == "__main__":
    cli(obj={})
