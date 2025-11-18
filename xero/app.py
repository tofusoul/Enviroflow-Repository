# -*- coding: utf-8 -*-
import os
from functools import wraps
from io import BytesIO
from logging.config import dictConfig
from streamlit import secrets
from flask import (
    Flask,
    url_for,
    render_template,
    session,
    redirect,
    json,
    send_file,
    request,
)
from flask_oauthlib.contrib.client import OAuth, OAuth2Application
from flask_session import Session
from xero_python.accounting import AccountingApi, ContactPerson, Contact, Contacts
from xero_python.api_client import ApiClient, serialize
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.exceptions import AccountingBadRequestException
from xero_python.identity import IdentityApi
from xero_python.utils import getvalue

import logging_settings
from utils import jsonify, serialize_model

dictConfig(logging_settings.default_settings)

# configure main flask application

app = Flask(__name__)
app.config.from_object("default_settings")
app.config.from_pyfile("config.py", silent=True)

# Load Xero credentials from Streamlit secrets
XERO_CLIENT_ID = secrets["xero"]["CLIENT_ID"]
XERO_CLIENT_SECRET = secrets["xero"]["CLIENT_SECRET"]

if app.config["ENV"] != "production":
    # allow oauth2 loop to run over http (used for local testing only)
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# configure persistent session cache
Session(app)

# configure flask-oauthlib application
# TODO fetch config from https://identity.xero.com/.well-known/openid-configuration #1

oauth = OAuth(app)

xero = OAuth2Application(
    app,
    client_id=XERO_CLIENT_ID,
    client_secret=XERO_CLIENT_SECRET,
    endpoint_url="https://api.xero.com/",
    authorization_url="https://login.xero.com/identity/connect/authorize",
    access_token_url="https://identity.xero.com/connect/token",
    refresh_token_url="https://identity.xero.com/connect/token",
    scope="openid accounting.settings.read profile files accounting.contacts.read email accounting.settings payroll.settings accounting.attachments.read accounting.budgets.read payroll.payruns accounting.journals.read assets.read payroll.timesheets accounting.contacts projects accounting.transactions.read assets payroll.payslip accounting.transactions accounting.reports.read files.read projects.read offline_access payroll.employees accounting.attachments",
)


# configure xero-python sdk client

api_client = ApiClient(
    Configuration(
        debug=app.config["DEBUG"],
        oauth2_token=OAuth2Token(
            client_id=XERO_CLIENT_ID, client_secret=XERO_CLIENT_SECRET
        ),
    ),
    pool_threads=1,
)


# configure token persistence and exchange point between flask-oauthlib and xero-python
@xero.tokengetter
@api_client.oauth2_token_getter
def obtain_xero_oauth2_token():
    return session.get("token")


@xero.tokensaver
@api_client.oauth2_token_saver
def store_xero_oauth2_token(token):
    session["token"] = token
    session.modified = True


def xero_token_required(function):
    @wraps(function)
    def decorator(*args, **kwargs):
        xero_token = obtain_xero_oauth2_token()
        if not xero_token:
            return redirect(url_for("login", _external=True))

        return function(*args, **kwargs)

    return decorator


@app.route("/")
def index():
    xero_access = dict(obtain_xero_oauth2_token() or {})
    return render_template(
        "code.html",
        title="Home | oauth token",
        code=json.dumps(xero_access, sort_keys=True, indent=4),
    )


@app.route("/tenants")
@xero_token_required
def tenants():
    identity_api = IdentityApi(api_client)
    accounting_api = AccountingApi(api_client)

    available_tenants = []
    connections = identity_api.get_connections()
    if connections is None:
        pass
    elif isinstance(connections, (list, tuple)):
        for connection in connections:
            tenant = serialize(connection)
            if getattr(connection, "tenant_type", None) == "ORGANISATION":
                organisations = accounting_api.get_organisations(
                    xero_tenant_id=getattr(connection, "tenant_id", None)
                )
                tenant["organisations"] = serialize(organisations)
            available_tenants.append(tenant)
    elif hasattr(connections, "tenant_type"):
        tenant = serialize(connections)
        if getattr(connections, "tenant_type", None) == "ORGANISATION":
            organisations = accounting_api.get_organisations(
                xero_tenant_id=getattr(connections, "tenant_id", None)
            )
            tenant["organisations"] = serialize(organisations)
        available_tenants.append(tenant)

    return render_template(
        "code.html",
        title="Xero Tenants",
        code=json.dumps(available_tenants, sort_keys=True, indent=4),
    )


@app.route("/create-contact-person")
@xero_token_required
def create_contact_person():
    xero_tenant_id = get_xero_tenant_id()
    accounting_api = AccountingApi(api_client)

    contact_person = ContactPerson(
        first_name="John",
        last_name="Smith",
        email_address="john.smith@24locks.com",
        include_in_emails=True,
    )
    contact = Contact(
        name="FooBar",
        first_name="Foo",
        last_name="Bar",
        email_address="ben.bowden@24locks.com",
        contact_persons=[contact_person],
    )
    contacts = Contacts(contacts=[contact])
    try:
        created_contacts = accounting_api.create_contacts(
            xero_tenant_id, contacts=contacts
        )
    except AccountingBadRequestException as exception:
        reason = getattr(exception, "reason", "")
        sub_title = f"Error: {reason}"
        code = jsonify(getattr(exception, "error_data", {}))
    else:
        name = (
            getvalue(getattr(created_contacts, "contacts", [{}]), "0.name", "")
            if hasattr(created_contacts, "contacts")
            else ""
        )
        sub_title = f"Contact {name} created."
        code = serialize_model(created_contacts)

    return render_template(
        "code.html", title="Create Contacts", code=code, sub_title=sub_title
    )


@app.route("/create-multiple-contacts")
@xero_token_required
def create_multiple_contacts():
    xero_tenant_id = get_xero_tenant_id()
    accounting_api = AccountingApi(api_client)

    contact = Contact(
        name="George Jetson",
        first_name="George",
        last_name="Jetson",
        email_address="george.jetson@aol.com",
    )
    # Add the same contact twice - the first one will succeed, but the
    # second contact will fail with a validation error which we'll show.
    contacts = Contacts(contacts=[contact, contact])
    try:
        created_contacts = accounting_api.create_contacts(
            xero_tenant_id, contacts=contacts
        )
    except AccountingBadRequestException as exception:
        reason = getattr(exception, "reason", "")
        sub_title = f"Error: {reason}"
        result_list = None
        code = jsonify(getattr(exception, "error_data", {}))
    else:
        sub_title = ""
        result_list = []
        contacts_list = (
            getattr(created_contacts, "contacts", [])
            if hasattr(created_contacts, "contacts")
            else []
        )
        for contact in contacts_list:
            if getattr(contact, "has_validation_errors", False):
                error = getvalue(
                    getattr(contact, "validation_errors", [{}]), "0.message", ""
                )
                result_list.append(f"Error: {error}")
            else:
                result_list.append(f"Contact {getattr(contact, 'name', '')} created.")
        code = serialize_model(created_contacts)

    return render_template(
        "code.html",
        title="Create Multiple Contacts",
        code=code,
        result_list=result_list,
        sub_title=sub_title,
    )


@app.route("/invoices")
@xero_token_required
def get_invoices():
    xero_tenant_id = get_xero_tenant_id()
    accounting_api = AccountingApi(api_client)

    invoices = accounting_api.get_invoices(xero_tenant_id)
    code = serialize_model(invoices)
    invoices_list = getattr(invoices, "invoices", [])
    if not isinstance(invoices_list, (list, tuple)):
        invoices_list = []
    sub_title = f"Total invoices found: {len(invoices_list)}"

    return render_template(
        "code.html", title="Invoices", code=code, sub_title=sub_title
    )


@app.route("/login")
def login():
    redirect_url = url_for("oauth_callback", _external=True)
    response = xero.authorize(callback_uri=redirect_url)
    return response


@app.route("/callback")
def oauth_callback():
    try:
        response = xero.authorized_response()
    except Exception as e:
        print(e)
        raise
    # todo validate state value
    if response is None or response.get("access_token") is None:
        return "Access denied: response=%s" % response
    store_xero_oauth2_token(response)
    return redirect(url_for("index", _external=True))


@app.route("/logout")
def logout():
    store_xero_oauth2_token(None)
    return redirect(url_for("index", _external=True))


@app.route("/export-token")
@xero_token_required
def export_token():
    token = obtain_xero_oauth2_token()
    buffer = BytesIO("token={!r}".format(token).encode("utf-8"))
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="x.python",
        as_attachment=True,
        download_name="oauth2_token.py",
    )


@app.route("/refresh-token")
@xero_token_required
def refresh_token():
    xero_token = obtain_xero_oauth2_token()
    new_token = api_client.refresh_oauth2_token()
    return render_template(
        "code.html",
        title="Xero OAuth2 token",
        code=jsonify({"Old Token": xero_token, "New token": new_token}),
        sub_title="token refreshed",
    )


@app.route("/all_quotes", methods=["GET", "POST"])
@xero_token_required
def get_all_quotes():
    from xero_quotes import Xero_Quotes_List

    xero_tenant_id = get_xero_tenant_id()
    if not xero_tenant_id:
        return render_template(
            "show_quotes.html",
            title="Quotes",
            code="",
            data=None,
            sub_title="",
            message="Error: Missing Xero tenant ID. Please ensure you are connected to a Xero organisation.",
            show_button=True,
        )
    accounting_api = AccountingApi(api_client)
    if request.method == "POST" and request.form.get("submit_button") == "Fetch JSON":
        all_quotes = []
        from xero_python.api_client import serialize

        page = 1
        while True:
            try:
                result = accounting_api.get_quotes(xero_tenant_id, page=page)  # type: ignore
                quotes = getattr(result, "quotes", [])
                if not quotes:
                    break
                all_quotes.extend([serialize(q) for q in quotes])
                page += 1
            except Exception as e:
                print(f"Error fetching quotes on page {page}: {e}")
                break
        if not all_quotes:
            return render_template(
                "show_quotes.html",
                title="Quotes",
                code="No quotes found.",
                data=None,
                sub_title="",
                message="No quotes found.",
                show_button=True,
            )
        quotes_list_obj = Xero_Quotes_List(all_quotes)
        df_human = getattr(quotes_list_obj, "quotes_df_human", None)
        import pandas as pd

        full_lines = []
        if hasattr(quotes_list_obj, "quotes_list"):
            for q in quotes_list_obj.quotes_list:
                if hasattr(q, "quote_lines_df") and q.quote_lines_df is not None:
                    full_lines.append(q.quote_lines_df)
        df_full = pd.concat(full_lines, ignore_index=True) if full_lines else None
        success_msg = ""
        # Filter out deleted quotes before saving to MotherDuck
        if df_full is not None and "quote_status" in df_full.columns:
            df_full = df_full[df_full["quote_status"] != "DELETED"]
        if df_human is not None and "quote_status" in df_human.columns:
            df_human = df_human[df_human["quote_status"] != "DELETED"]
        try:
            from enviroflow_app.elt.motherduck.md import MotherDuck

            md_token = secrets["motherduck"]["token"]
            md_db = secrets["motherduck"]["db"]
            md = MotherDuck(token=md_token, db_name=md_db)
            import polars as pl

            if df_human is not None:
                md.save_table("xero_quotes", pl.DataFrame(df_human))
            if df_full is not None:
                md.save_table("full_xero_quotes", pl.DataFrame(df_full))
            success_msg = (
                "✅ Successfully saved xero_quotes and full_xero_quotes to MotherDuck."
            )
        except Exception as e:
            success_msg = f"MotherDuck save error: {e}"

        df_head_html = "No DataFrame available."
        # Always filter out deleted quotes before displaying
        df_full_display = (
            df_full[df_full["quote_status"] != "DELETED"]
            if df_full is not None and "quote_status" in df_full.columns
            else df_full
        )
        if df_full_display is not None and "quote_no" in df_full_display.columns:
            df_head = df_full_display.sort_values(by="quote_no", ascending=False).head()
            df_head_html = df_head.to_html(index=False)
        sub_title = f"Total number of quotes: {len(all_quotes)}"
        message = f"Quotes Loaded<br>{success_msg}"
        return render_template(
            "show_quotes.html",
            title="Quotes",
            code="Head of full_xero_quotes table:",
            data=df_head_html,
            sub_title=sub_title,
            message=message,
            show_button=True,
        )
    # GET request: show button and empty pane
    return render_template(
        "show_quotes.html",
        title="Quotes",
        code="",
        data=None,
        sub_title="",
        message="Click the button to fetch quotes.",
        show_button=True,
    )


def get_xero_tenant_id():
    token = obtain_xero_oauth2_token()
    if not token:
        return None

    identity_api = IdentityApi(api_client)
    connections = identity_api.get_connections()
    if connections is None:
        return None
    # If connections is iterable and not a string, iterate
    if isinstance(connections, (list, tuple)):
        for connection in connections:
            if getattr(connection, "tenant_type", None) == "ORGANISATION":
                return getattr(connection, "tenant_id", None)
    elif hasattr(connections, "tenant_type"):
        if getattr(connections, "tenant_type", None) == "ORGANISATION":
            return getattr(connections, "tenant_id", None)


@app.route("/quotes")
@xero_token_required
def get_quotes():
    # add a datepicker https://www.youtube.com/watch?v=jAdFZa6KZNE
    xero_tenant_id = get_xero_tenant_id()
    accounting_api = AccountingApi(api_client)

    xero_tenant_id = get_xero_tenant_id()
    if not xero_tenant_id:
        return render_template(
            "show_quotes.html",
            title="Quotes",
            code="",
            sub_title="",
            data=None,
            message="Error: Missing Xero tenant ID. Please ensure you are connected to a Xero organisation.",
        )
    result = accounting_api.get_quotes(xero_tenant_id)
    quotes = getattr(result, "quotes", [])
    code = serialize_model(result)
    sub_title = "Total quotes found: {}".format(len(quotes))
    data = "nothing to see yet!"
    return render_template(
        "show_quotes.html",
        title="updated_quotes",
        code=code,
        sub_title=sub_title,
        data=data,
    )


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
