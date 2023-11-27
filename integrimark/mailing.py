import csv
import datetime
import os
import json
import pkg_resources
import re
import typing

import integrimark.encryption

import dotenv
import gspread
import jinja2
import loguru
import markdownify
import tqdm


def current_millisecond_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


# Function to get the column index
def get_column_index(column, header=None):
    if isinstance(column, int) or (isinstance(column, str) and column.isdigit()):
        column = int(column)
        return column
    elif isinstance(column, str):
        if header is None:
            raise ValueError(
                "Header must be provided if column is referenced by a string"
            )
        return header.index(column)
    else:
        raise ValueError("COLUMN_EMAIL and COLUMN_FILES must be an int or str")


def get_gspread_service_account(service_account_json_path=None):
    # path provided and it exists
    if service_account_json_path is not None and os.path.exists(
        service_account_json_path
    ):
        loguru.logger.info(f"GSpread auth: Using {service_account_json_path}")
        return gspread.service_account(filename=service_account_json_path)

    # path not provided look at SERVICE_ACCOUNT_JSON environment variable
    if os.environ.get("SERVICE_ACCOUNT_JSON") is not None:
        service_account_json = json.loads(os.environ.get("SERVICE_ACCOUNT_JSON"))
        loguru.logger.info(
            "GSpread auth: Using SERVICE_ACCOUNT_JSON environment variable"
        )
        return gspread.service_account_from_dict

    loguru.logger.info("GSpread auth: No credentials provided, cannot retrieve data")
    raise ValueError("No credentials provided, cannot retrieve data")


# Function to load spreadsheet data
def load_spreadsheet(
    google_spreadsheet_id,
    google_worksheet_index,
    email_col,
    files_col,
    service_account_json_path=None,
    no_header=False,
):
    gc = get_gspread_service_account(
        service_account_json_path=service_account_json_path
    )
    ssheet = gc.open_by_key(google_spreadsheet_id)
    worksheet = ssheet.get_worksheet(google_worksheet_index)

    # Determine column indices
    header = None
    if not no_header:
        header = worksheet.row_values(1)

    email_col_index = get_column_index(column=email_col, header=header)
    files_col_index = (
        get_column_index(column=files_col, header=header)
        if files_col is not None
        else None
    )

    # Fetch rows
    rows = worksheet.get_all_values()[1:]  # Exclude header

    # Modified records
    records = [
        {
            "email": row[email_col_index],
            "files": row[files_col_index] if files_col is not None else None,
            "row": row,
            "rowdict": dict(zip(header, row)) if header else None,
        }
        for row in rows
    ]

    return records


# Function to generate URLs for files
def get_urls_for_email(email, passwords_data):
    base_url = passwords_data["base_url"]
    routing = passwords_data["routing"]
    passwords = passwords_data["passwords"]

    files = []
    for public_filename, private_filename in routing.items():
        password = passwords.get(private_filename)
        if not password:
            raise ValueError(f"Missing password for {private_filename}")
        url = integrimark.encryption.generate_url(
            email=email,
            password=password,
            base_url=base_url,
            file=public_filename,
        )
        files.append({"description": public_filename, "href": url})
    return files


def send_email_with_sendgrid(
    to_email, subject, html_content, from_email=None, api_key=None, cc_from=False
):
    import sendgrid
    import sendgrid.helpers.mail

    if api_key is None:
        api_key = os.environ.get("SENDGRID_API_KEY")
        if api_key is None:
            loguru.logger.warning(
                "SENDGRID_API_KEY is not provided through command-line or found in environment variables. Please set it."
            )
            return False

    if from_email is None:
        from_email = os.environ.get("EMAIL_FROM_SENDER")
        if from_email is None:
            loguru.logger.warning(
                "EMAIL_FROM_SENDER is not provided through command-line or found in environment variables. Please set it."
            )
            return False

    sg = sendgrid.SendGridAPIClient(api_key)

    # Convert HTML to plain text
    text_content = markdownify.markdownify(html_content)

    message = sendgrid.helpers.mail.Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
        plain_text_content=text_content,
    )
    if cc_from:
        message.add_cc(from_email)

    # Configure tracking settings (improve spam perception score)
    tracking_settings = sendgrid.helpers.mail.TrackingSettings()
    tracking_settings.click_tracking = sendgrid.helpers.mail.ClickTracking(
        enable=False, enable_text=False
    )
    tracking_settings.open_tracking = sendgrid.helpers.mail.OpenTracking(enable=False)
    message.tracking_settings = tracking_settings
    message.add_header(sendgrid.helpers.mail.Header("List-Unsubscribe", from_email))

    response = sg.send(message)

    return response.status_code == 202


def send_email_with_smtplib(
    to_email,
    subject,
    html_content,
    from_email=None,
    smtp_server=None,
    smtp_port=587,
    username=None,
    password=None,
    cc_from=False,
):
    import smtplib
    import email.mime.multipart
    import email.mime.text

    # Environment Variables for SMTP credentials and sender email
    if from_email is None:
        from_email = os.environ.get("EMAIL_FROM_SENDER")
        if from_email is None:
            loguru.logger.warning(
                "EMAIL_FROM_SENDER is not provided through command-line or found in environment variables. Please set it."
            )
            return False

    if smtp_server is None:
        smtp_server = os.environ.get("SMTP_SERVER")
        if smtp_server is None:
            loguru.logger.warning(
                "SMTP_SERVER is not provided through command-line or found in environment variables. Please set it."
            )
            return False

    if username is None:
        username = os.environ.get("SMTP_USERNAME")
        if username is None:
            loguru.logger.warning(
                "SMTP_USERNAME is not provided through command-line or found in environment variables. Please set it."
            )
            return False

    if password is None:
        password = os.environ.get("SMTP_PASSWORD")
        if password is None:
            loguru.logger.warning(
                "SMTP_PASSWORD is not provided through command-line or found in environment variables. Please set it."
            )
            return False

    # Convert HTML to plain text
    text_content = markdownify.markdownify(html_content)

    # Create message container
    msg = email.mime.multipart.MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    # Record the MIME types
    part1 = email.mime.text.MIMEText(text_content, "plain")
    part2 = email.mime.text.MIMEText(html_content, "html")

    msg.attach(part1)
    msg.attach(part2)

    # Add CC if required
    if cc_from:
        msg.add_header("CC", from_email)
        to_email = [to_email, from_email]  # Include in recipient list

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_email, to_email, msg.as_string())
        return True
    except Exception as e:
        loguru.logger.error(f"An error occurred: {e}")
        return False


def get_integrimark_mailer_template(template_file=None):
    """Returns the integrimark HTML template."""
    try:
        filename = template_file or pkg_resources.resource_filename(
            package_or_requirement=__name__,
            resource_name="integrimark.solutions-email.jinja2.html",
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
            return jinja2.Template(content)
    except Exception as e:
        loguru.logger.error(f"Error in getting integrimark template: {e}")
        raise


#
# { "processed": { 1: { "email": "email", "ts": "timestamp" } },
# "errors": [ { "email": "email", "ts": "timestamp", "error": "error", "row": 1 } ]


def check_email_has_been_sent(email_status_file, email, row_id):
    if not os.path.exists(email_status_file):
        return False

    with open(email_status_file, "r") as f:
        data = json.load(f)
        row_id_is_processed = data["processed"].get(row_id) is not None
        row_id_is_consistent = data["processed"].get(row_id, {}).get("email") == email
        return row_id_is_processed and row_id_is_consistent


def record_email_status(email_status_file, email, row_id, success=False, error=None):
    if not os.path.exists(email_status_file):
        data = {"processed": {}, "errors": []}
    else:
        try:
            with open(email_status_file, "r") as f:
                data = json.load(f)
        except Exception as e:
            loguru.logger.error(f"Error in loading email status file: {e}")
            pass

    if success:
        data["processed"][row_id] = {
            "email": email,
            "ts": current_millisecond_timestamp(),
        }
    else:
        data["errors"].append(
            {
                "email": email,
                "ts": current_millisecond_timestamp(),
                "error": error,
                "row": row_id,
            }
        )

    with open(email_status_file, "w") as f:
        json.dump(data, f, indent=2)


def extract_title_from_html(html: str) -> typing.Optional[str]:
    """
    Extract title from an HTML document.

    :param html: The HTML document
    :type html: str

    :return: A title, if one is found; `None` otherwise
    :rtype: typing.Optional[str]
    """
    match = re.search(r"<title>([^<]*)</title>", html)

    # no match found: return empty string
    if match is None:
        return

    # match found: extract first group
    raw_title = match.group(1)

    # clean-up title
    title = re.sub(r"\s+", " ", raw_title).strip()

    # If empty string, just return None
    if title == "":
        return

    return title


def load_csv_data(csv_file_path, email_col, files_col, no_header=False):
    with open(csv_file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        rows = list(reader)

    header = rows[0] if not no_header else None
    data_start_index = 1 if not no_header else 0

    email_col_index = get_column_index(column=email_col, header=header)
    files_col_index = (
        get_column_index(column=files_col, header=header)
        if files_col is not None
        else None
    )

    records = [
        {
            "email": row[email_col_index],
            "files": row[files_col_index] if files_col is not None else None,
            "row": row,
            "rowdict": dict(zip(header, row)) if header else None,
        }
        for row in rows[data_start_index:]
    ]

    return records


def send_solution_mailers(
    email_col,
    files_col=None,
    passwords_file=None,
    from_email=None,
    subject="Your Requested Solutions",
    template_file=None,
    csv_input_file=None,
    google_spreadsheet_id=None,
    google_worksheet_index=0,
    service_account_json_path=None,
    sendgrid_api_key=None,
    smtp_server=None,
    smtp_port=587,
    smtp_username=None,
    smtp_password=None,
    email_status_file="email-status.json",
    no_send_mode=False,
):
    # Load spreadsheet data
    if google_spreadsheet_id is not None:
        records = load_spreadsheet(
            google_spreadsheet_id=google_spreadsheet_id,
            google_worksheet_index=google_worksheet_index,
            email_col=email_col,
            files_col=files_col,
            service_account_json_path=service_account_json_path,
        )

    elif csv_input_file is not None:
        records = load_csv_data(
            csv_file_path=csv_input_file,
            email_col=email_col,
            files_col=files_col,
        )

    else:
        loguru.logger.error(
            "GOOGLE_SPREADSHEET_ID or CSV_INPUT_FILE is not provided through command-line or found in environment variables. Please set it."
        )
        return False

    # Load passwords data
    if passwords_file is None or not os.path.exists(passwords_file):
        loguru.logger.error(
            "PASSWORDS_FILE is not provided through command-line or found in environment variables. Please set it."
        )
        return False

    with open(passwords_file, "r") as file:
        passwords_data = json.load(file)

    # Load email template
    template = get_integrimark_mailer_template(template_file=template_file)

    # Process and send emails
    for index, record in enumerate(tqdm.tqdm(records, desc="Sending Emails")):
        email = record["email"]

        # check if email has already been sent
        if check_email_has_been_sent(
            email_status_file=email_status_file, email=email, row_id=index
        ):
            loguru.logger.info(f"Email already sent to {email}. Skipping.")
            continue

        urls = get_urls_for_email(email, passwords_data)
        selected_urls = urls[:]

        if files_col is not None:
            # by default include all files, so there is no need for this field
            selected_files = record["files"].split(",")
            selected_urls = [
                url for url in urls if url["description"] in selected_files
            ]

        # Render email content
        content = template.render(email=email, selected_solution_links=selected_urls)
        subject = extract_title_from_html(content) or "Your Requested Solutions"

        if no_send_mode:
            loguru.logger.info(
                f"NoSendMode: Email not sent to {email}. Success: True. Subject: {subject}"
            )
            success = True
        else:
            if smtp_server is None or sendgrid_api_key is not None:
                success = send_email_with_sendgrid(
                    to_email=email,
                    subject=subject,
                    html_content=content,
                    from_email=from_email,
                    api_key=sendgrid_api_key,
                    cc_from=True,
                )

            else:
                success = send_email_with_smtplib(
                    to_email=email,
                    subject=subject,
                    html_content=content,
                    from_email=from_email,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    username=smtp_username,
                    password=smtp_password,
                    cc_from=True,
                )

        loguru.logger.info(
            f"Email sent to {email}. Success: {success}. Subject: {subject}"
        )

        record_email_status(
            email_status_file=email_status_file,
            email=email,
            row_id=index,
            success=success,
            error=None if success else "Email not sent",
        )
