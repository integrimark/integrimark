import integrimark.encryption

import csv
import os
import json
import pkg_resources
import urllib.parse

import click
import dotenv
import loguru
from click_help_colors import HelpColorsGroup, HelpColorsCommand
from xkcdpass import xkcd_password as xp


dotenv.load_dotenv()

# Configure loguru for colored output
loguru.logger.remove()
loguru.logger.add(lambda msg: click.echo(msg, nl=False), colorize=True)


def get_integrimark_template(base_url=None):
    """Returns the integrimark HTML template."""
    try:
        filename = pkg_resources.resource_filename(
            package_or_requirement=__name__, resource_name="integrimark.pack.html"
        )

        if not os.path.exists(filename):
            loguru.logger.error(
                "Integrimark template not found. Please reinstall integrimark. (File not found: {}.)".format(
                    filename
                )
            )
            raise FileNotFoundError

        with open(filename, "r") as f:
            content = f.read()
            if base_url:
                routingURL = urllib.parse.urljoin(base_url, "routing.js")
                content = content.replace('"routing.js"', f'"{routingURL}"')
            return content
    except Exception as e:
        loguru.logger.error(f"Error in getting integrimark template: {e}")
        raise


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def cli():
    """
    INTEGRIMARK, document watermarking distribution tool
    https://github.com/jlumbroso/integrimark

    Distribute watermarked documents from GitHub pages using an encrypted bundle.
    Built with love by Jérémie Lumbroso <lumbroso@seas.upenn.edu>, feedback welcome.
    """
    pass


@cli.command(cls=HelpColorsCommand, help_options_color="bright_green")
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-o",
    "--output_directory",
    default=os.getcwd(),
    type=click.Path(exists=True),
    help="Directory where _bundle folder will be created. Defaults to the current working directory.",
)
@click.option(
    "-u",
    "--base_url",
    default=None,
    type=click.STRING,
    help="Base URL at which the Integrimark vault will be hosted.",
)
@click.option(
    "--refresh",
    is_flag=True,
    default=False,
    help="Generate new passwords for all files, even if they exist in the _bundle.",
)
def create(files, output_directory, base_url, refresh):
    """Encrypts provided PDF files and saves them in the _bundle directory."""
    bundle_path = os.path.join(output_directory, "_bundle")
    password_path = os.path.join(bundle_path, "passwords.json")

    if not os.path.exists(bundle_path):
        os.makedirs(bundle_path)

    # Load existing passwords if available and --no-refresh is set
    if not refresh and os.path.exists(password_path):
        with open(password_path, "r") as f:
            full_password_file = json.load(f)
        passwords = full_password_file.get("passwords", {})
    else:
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

        # Use existing password if available and --no-refresh is set
        if output_filename in passwords and not refresh:
            password = passwords[output_filename]
            loguru.logger.info(f"Using existing password: {password}")
        else:
            password = xp.generate_xkcdpassword(wordlist, numwords=4)
            passwords[output_filename] = password
            loguru.logger.info(f"Generated password: {password}")

        integrimark.encryption.encrypt_pdf_file(
            input_file=file, password=password, output_file=output_path
        )

        new_name = base_name
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
                f.write("\npasswords.json")
    else:
        with open(gitignore_path, "w") as f:
            f.write("\n_bundle/passwords.json")
            f.write("\npasswords.json")

    click.echo(click.style("Encryption complete!", fg="green"))


@cli.command(cls=HelpColorsCommand, help_options_color="bright_green")
@click.argument("bundle_path", type=click.Path(exists=True))
@click.argument("email_addresses", nargs=-1, type=click.STRING)
@click.option(
    "-f",
    "--file_name",
    multiple=True,
    type=click.STRING,
    help="Name of the file (e.g., 'HW1-SOLUTIONS'). Can be used multiple times for multiple files.",
)
@click.option(
    "-o",
    "--csv-output",
    type=click.Path(),
    help="Optional: Output CSV file name for storing the URLs.",
)
def url(bundle_path, email_addresses, file_name, csv_output):
    """Generates URLs for the given email addresses and file names."""
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

    url_data = []
    for email in email_addresses:
        row = {"email": email}
        for name in file_names:
            encrypted_file_name = routing.get(name)
            if encrypted_file_name:
                password = passwords.get(encrypted_file_name)
                if password:
                    encrypted_url = integrimark.encryption.generate_url(
                        email, password, base_url, name
                    )
                    click.echo(
                        "URL of {} customized for {}: {}".format(
                            name, email, encrypted_url
                        )
                    )
                    loguru.logger.info(f"Generated URL for {name}")
                    row[name] = encrypted_url
                else:
                    loguru.logger.warning(f"Password not found for file {name}.")
            else:
                loguru.logger.warning(f"File name {name} not found in routing.")
        url_data.append(row)

    if csv_output:
        with open(csv_output, mode="w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["email"] + list(file_names))
            writer.writeheader()
            for row in url_data:
                writer.writerow(row)
            click.echo(click.style(f"URLs saved to {csv_output}", fg="green"))


if __name__ == "__main__":
    cli()
