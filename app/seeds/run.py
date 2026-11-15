
import typer

from app.seeds.service import run_all, run_categories, run_tags, run_users


app = typer.Typer(help="Seeds: users, categories, tags")

@app.command("all")
def all_():
    run_all()
    typer.echo("Seeds cargados exitosamente.")

@app.command("users")
def users():
    run_users()
    typer.echo("Users cargados exitosamente.")

@app.command("categories")
def categories():
    run_categories()
    typer.echo("Categories cargadas exitosamente.")

@app.command("tags")
def tags():
    run_tags()
    typer.echo("Tags cargados exitosamente.")