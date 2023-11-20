import integrimark.encryption

import os
import json
import pkg_resources
import urllib.parse

import click
import dotenv
import loguru
from xkcdpass import xkcd_password as xp


dotenv.load_dotenv()


def get_integrimark_template(base_url=None):
    """Returns the integrimark HTML template."""
    try:
        filename = pkg_resources.resource_filename(
            package_or_requirement=__name__, resource_name="integrimark.pack.html"
        )

        with open(filename, "r") as f:
            content = f.read()
            if base_url:
                routingURL = urllib.parse.urljoin(base_url, "routing.js")
                content = content.replace('"routing.js"', f'"{routingURL}"')
            return content
    except Exception as e:
        loguru.logger.error(f"Error in getting integrimark template: {e}")
        raise


@click.group()
def cli():
    """Integrimark command line tool."""
    pass


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-o",
    "--output_Directory",
    default=os.getcwd(),
    type=click.Path(exists=True),
    help="Directory where _bundle folder will be created. Defaults to the current working directory.",
)
@click.option(
    "-u",
    "--base_URL",
    default=None,
    type=click.STRING,
    help="Base URL at which the Integrimark vault will be hosted.",
)
def create(files, output_directory, base_url):
    """Encrypts provided PDF files and saves them in the _bundle directory."""
    bundle_path = os.path.join(output_directory, "_bundle")

    if not os.path.exists(bundle_path):
        os.makedirs(bundle_path)

    passwords = {}
    routing = {}

    # load wordfiles
    wordfile = xp.locate_wordfile()
    wordlist = open(wordfile).read().splitlines(keepends=False)

    # Process files
    for file in files:
        base_name = os.path.basename(file)

        file_hash = integrimark.encryption.md5_hash_file(file)

        output_filename = "_{}.enc.pdf".format(file_hash)
        output_path = os.path.join(bundle_path, output_filename)

        # Check if password is provided, if not generate one
        password = xp.generate_xkcdpassword(wordlist, numwords=4)
        passwords[output_filename] = password
        loguru.logger.info(f"Generated password: {password}")

        integrimark.encryption.encrypt_pdf_file(
            input_file=file, password=password, output_file=output_path
        )

        new_name = base_name.split(".")[0].upper()
        routing[new_name] = output_filename

    # Duplicate integrimark page
    html_file_path = os.path.join(bundle_path, "404.html")
    with open(html_file_path, "w") as f:
        f.write(get_integrimark_template(base_url=base_url))

    routing_path = os.path.join(bundle_path, "routing.js")
    with open(routing_path, "w") as f:
        f.write("var integrimarkRoutes = ")
        f.write(json.dumps(routing, indent=2))
        f.write(";\n\n")
        f.write("var integrimarkBaseURL = '{}'".format(base_url or ""))
        f.close()

    # create .nojekyll file
    nojekyll_path = os.path.join(bundle_path, ".nojekyll")
    with open(nojekyll_path, "w") as f:
        f.write("")

    # save passwords and ensuring .gitignore
    print(json.dumps(passwords, indent=2))
    password_path = os.path.join(bundle_path, "passwords.json")
    full_password_file = {
        "manifestVersion": 1,
        "passwords": passwords,
        "base_url": base_url,
        "routing": routing,
    }
    with open(password_path, "w") as f:
        f.write(json.dumps(full_password_file, indent=2))
        f.close()

    gitignore_path = os.path.join(bundle_path, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            lines = f.readlines()

        if "_bundle/passwords.json" not in lines or "passwords.json" not in lines:
            with open(gitignore_path, "a") as f:
                f.write("\n_bundle/passwords.json")
                f.write("\n/passwords.json")
    else:
        with open(gitignore_path, "w") as f:
            f.write("_bundle/passwords.json")
            f.write("passwords.json")

    click.echo("Encryption complete!")


@cli.command()
@click.argument("bundle_path", type=click.Path(exists=True))
@click.argument("email_address", type=click.STRING)
@click.option(
    "-f",
    "--file_name",
    multiple=True,
    type=click.STRING,
    help="Name of the file (e.g., 'HW1-SOLUTIONS'). Can be used multiple times for multiple files.",
)
def url(bundle_path, email_address, file_name):
    """Generates URLs for the given email address and file names."""
    password_file = os.path.join(bundle_path, "passwords.json")

    if not os.path.exists(password_file):
        loguru.logger.error(
            "No password file found. Please run 'create' command first."
        )
        return

    with open(password_file, "r") as f:
        data = json.load(f)

    passwords = data.get("passwords", {})
    base_url = data.get("base_url", "")
    routing = data.get("routing", {})

    file_names = file_name if file_name else routing.keys()

    for name in file_names:
        public_file_name = name + ".pdf"
        encrypted_file_name = routing.get(name.upper())
        if encrypted_file_name:
            password = passwords.get(encrypted_file_name)
            if password:
                encrypted_url = integrimark.encryption.generate_url(
                    email_address, password, base_url, public_file_name
                )
                click.echo(
                    "URL of {} customized for {}: {}".format(
                        name, email_address, encrypted_url
                    )
                )
                loguru.logger.info(f"Generated URL for {name}")
            else:
                loguru.logger.warning(f"Password not found for file {name}.")
        else:
            loguru.logger.warning(f"File name {name} not found in routing.")


if __name__ == "__main__":
    cli()
