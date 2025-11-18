import copy
from datetime import date, timedelta

import pandas as pd
import polars as pl
import streamlit as st
from loguru import logger

# Quote lookup configuration
from enviroflow_app.model.quote import QUOTE_LOOKUP

# from deta import Deta
from enviroflow_app import config
from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.transform.from_projects_data import Projects_Data
from enviroflow_app.elt.transform.from_sub_con_data import From_Subs_Rates
from enviroflow_app.model import Project, Quote, merge_quotes
from enviroflow_app.st_components import pre, widgets

logger.configure(**config.APP_LOG_CONF)
pre.setup_streamlit_page()
pre.init_default_session()
SESSION_KEYS = ["projects_dict", "status", "sub", "proj", "form", "manual_input"]
pre.set_session_keys(SESSION_KEYS)
tables = [
    "quotes",
    "projects",
    "labour_hours",
    "jobs_for_analytics",
    "xero_costs",
    "subs_details",
    "subs_rates",
]
with st.spinner("loading source data from DB ..."):
    pre.load_md_data_to_session_state(tables)
ss = st.session_state
conn: md.MotherDuck = ss.db_conn
ss.manual_input = False
projects_df: pl.DataFrame = ss.projects
quotes_df: pl.DataFrame = ss.quotes
jobs_df: pl.DataFrame = ss.jobs_for_analytics
labour_hours_df = ss.labour_hours
costs_df = ss.xero_costs

with st.sidebar:
    st.toggle("toggle Dev Mode", key="dev")
if ss.dev:
    st.write(ss)

if ss.projects_dict is None:
    with st.spinner("Building Project Data"):
        projects: dict[str, Project] = Projects_Data(
            projects_df=projects_df,
            jobs_df=jobs_df,
            quotes_df=quotes_df,
            labour_hours_df=labour_hours_df,
            costs_df=costs_df,
        ).projects_dict
        ss.projects_dict = projects


def titlebar():
    st.title("📝Subcontract Generator")
    "---"


default = "1/40 Maryhill + 2/40 Maryhill"
projects: dict[str, Project] = ss.projects_dict
subs_details: pl.DataFrame = ss.subs_details
subs_rates: pl.DataFrame = ss.subs_rates
subs_names = subs_details["Business"].to_list()


#
# if selected_project_name is not None:
#     selected_project = projects[selected_project_name]
#     widgets.render_project_links(project=selected_project)
#
def enter_project_info(
    projects: dict[str, Project],
    subs_names: list[str],
):
    project_names = list(projects.keys())
    project_names.insert(0, "")

    st.write("### 1. Enter Project Info")
    notification_area = st.empty()
    with st.form(key="generate_subcontract"):
        project_selected = st.selectbox(
            "Select project to send to subcontractor",
            project_names,
        )
        subcon_name = st.selectbox("Select Subcontractor", subs_names)
        pm = st.selectbox(
            "Select Project Manager:",
            [
                "Brendan",
                "Shea",
                "Andy",
                "Hayden",
                "Ryan",
            ],
        )
        col1, col2 = st.columns(2)
        with col1:
            completed_by = st.date_input(
                "Project to Be Completed By:",
                value=date.today() + timedelta(days=10),
                help="Defaults to 10 days from Today",
            )
        with col2:
            to_phone = st.checkbox("Sub needs to call before Starting")

        additional_info = st.text_area(
            "Additional info/ instructions, please write complete paragrapchs",
        )

        st.checkbox("Manual Input", key="manual_input")
        submit = st.form_submit_button(label="Next")
    if submit:
        # Package data
        if project_selected == "":
            with notification_area.container():
                st.error("⚠ No project selected- select a project and start again")

        else:
            form = {
                "date": date.today(),
                "project": project_selected,
                "subcontractor": subcon_name,
                "project_manager": pm,
                "completed_by": completed_by,
                "to_phone": to_phone,
                "additional_info": additional_info,
            }

            proj: Project = projects[project_selected]  # type: ignore
            st.session_state["form"] = form
            st.session_state["sub"] = subcon_name
            st.session_state["proj"] = proj
            st.session_state["status"] = "form_completed"


def clean_quote(df: pd.DataFrame, for_summary=False):
    df = df.copy()
    df.drop(columns=["customer", "quote_ref", "quote_source"], inplace=True)
    if for_summary:
        df.drop(columns=["quote_no"], inplace=True)
    return df


def change_status(status: str):
    st.session_state["status"] = status


def clear_job_selection():
    st.session_state["status"] = None
    st.session_state["proj"] = None
    st.session_state["form"] = None
    st.session_state["sub"] = None


def manual_qty_input(
    form_content: dict,
    project: Project,
    subcon: str,
    subs_rates_df: pl.DataFrame,
):
    updated_form = copy.deepcopy(form_content)
    st.button(
        "Back to Start",
        key="manual_input_to_start",
        on_click=clear_job_selection,
    )
    st.write("### ⚠️ No Quote Found, Please Enter Values Manually")
    st.info("press the `tab` key to jump to the next field")
    input_keys = []
    for i in QUOTE_LOOKUP:
        input_keys.append((i[0], i[1], i[3]))
    # TODO this whole pthing needs a re-write
    rates_dict = From_Subs_Rates(subs_rates_df, subcon).rates_dict
    with st.form(key="manual_qty_input"):
        for i in input_keys:
            st.number_input(label=f"**{i[1].title()}**", key=i[0], step=5)
        save_qty = st.form_submit_button(label="Save")
        if save_qty:
            sub_lines = {}
            sub_lines["se"] = {
                "line": "Site establishment",
                "qty": 1,
                "rate": rates_dict["se"],
            }
            for i in input_keys:
                if i[0] in st.session_state.keys():
                    try:
                        sub_lines[i[0]] = {
                            "line": i[2],
                            "qty": st.session_state[i[0]],
                            "rate": rates_dict[i[0]],
                        }
                    except KeyError:
                        sub_lines[i[0]] = {
                            "line": i[2],
                            "qty": st.session_state[i[0]],
                            "rate": None,
                        }

            sub_lines["asbuilt"] = {
                "line": "Provide PS3(Drainage Producer Statement) and As-Built",
                "qty": 1,
                "rate": rates_dict["asbuilt"],
            }

            updated_form["sub_lines"] = sub_lines
            updated_form["tags"] = []
            st.session_state["form"] = updated_form
            st.session_state["status"] = "details_checked"  # "qty_checked"


def check_qty(
    form_content: dict,
    project: Project,
    subcon: str,
    subs_rates_df: pl.DataFrame,
):
    st.write("### 2, 3. Check the Job Details of the Project")
    st.warning(
        "👇Check the summed quatities below, if anything is amiss, update them before continuing",
    )
    st.button("Back to Start", on_click=clear_job_selection)
    st.write(f"#### Project: *{project.name}*")
    widgets.render_project_links(project)

    quotes: list[Quote] = project.quotes if project.quotes is not None else []
    variation_quotes: list[Quote] = (
        project.variation_quotes if project.variation_quotes is not None else []
    )
    rates_dict = From_Subs_Rates(subs_rates_df, subcon).rates_dict
    # List the quotes read by the software
    st.write(f"{len(quotes)} quote(s) found for project")
    for quote in quotes:
        st.write(" ▶ " + quote.quote_ref)
    st.write(f"{len(variation_quotes)} variation quote(s) found for project")
    for quote in variation_quotes:
        st.write(" ▶ " + quote.quote_ref)

    all_quotes = quotes + variation_quotes
    updated_form = copy.deepcopy(form_content)
    for i, quote in enumerate(all_quotes):
        with st.expander(
            f"Quote: {quote.quote_no}: **{quote.quote_ref}** : (from {quote.quote_source})",
        ):
            # st.write(clean_quote(quote.quote_lines.to_pandas(), for_summary=True))
            st.write(quote.quote_lines)

    select_index = [(i, quote.quote_ref) for i, quote in enumerate(all_quotes)]
    selected_index = st.multiselect(
        "select quotes to add to subcon scope",
        options=select_index,
        default=select_index,
        format_func=lambda x: x[1],
    )
    selected_quotes = []

    for i in selected_index:
        selected_quotes.append(all_quotes[i[0]])

    total_quote: Quote = merge_quotes(quotes=selected_quotes, name=project.name)

    with st.form(key="check quantities are correct"):
        st.write("#### check subcontractor quantities")
        tags_area = st.empty()
        taglist = []
        for k, v in total_quote.quote_analysis.items():
            if v["has"]:
                if k in ["pipelining", "contaminated", "trench_shield"]:
                    taglist.append(k)
                else:
                    st.write(f"##### **{v['desc']}**:".title())
                    st.number_input(
                        f"Please check {v['desc']} quantity is correct:",
                        value=v["qty"],
                        key=k,
                        step=1.00,
                        label_visibility="collapsed",
                    )
                    st.write(v["df"].sort_values(by=["line_pct"]))
        tags_area.write(">" + ", ".join([f"[{i}]" for i in taglist]))
        # main_contact = (
        #     ss.subs_details.filter(pl.col("Business") == subcon)
        #     .select("Main Contact")
        #     .item()
        # )

        # st.write("##### **Additional Items to Add**".title())
        # items_to_add = st.number_input("how many items to add?", value=0, step=1)
        # function to add input fileds to add a custom item that is added to the final quantities table
        # item_name = st.text_input("Item to Add")
        # item_qty = st.number_input(
        #     f"Please check the quantity for **{item_name}** is correct:",
        #     value=1,
        #     step=1,
        # )
        #
        qty_ok = st.form_submit_button(label="Qty Ok")
        if qty_ok:
            sub_lines = {}
            sub_lines["se"] = {
                "line": "Site establishment",
                "qty": 1,
                "rate": rates_dict["se"],
            }
            for k, v in total_quote.quote_analysis.items():
                if k in st.session_state.keys():
                    sub_lines[k] = {
                        "line": v["sub"],
                        "qty": st.session_state[k],
                        "rate": rates_dict[k],
                    }
            sub_lines["asbuilt"] = {
                "line": "Provide PS3(Drainage Producer Statement) and As-Built",
                "qty": 1,
                "rate": rates_dict["asbuilt"],
            }

            updated_form["sub_lines"] = sub_lines
            updated_form["tags"] = taglist
            st.session_state["form"] = updated_form
            st.session_state["status"] = "details_checked"  # "qty_checked"


def render_contact_details_test(project: Project):
    if project.jobs is not None and project.jobs != []:
        for job in project.jobs:
            st.write(job.customer_details)


def render_contact_details(project: Project) -> None:
    st.write("Contact details for the owner(s) are:")
    if project.jobs is not None and project.jobs != []:
        for job in project.jobs:
            if job is not None:
                st.write(f"**{job.name}**")
                if job.customer_details is not None:
                    try:
                        if job.customer_details["name"] is not None:
                            st.write(f"- {job.customer_details['name']}")
                    except Exception:
                        logger.error(f"{job.name} does not have a customer name")
                    try:
                        if job.customer_details["phone"] is not None:
                            st.write(f"- {job.customer_details['phone']}")
                    except Exception:
                        logger.error(f"{job.name} does not have a phone")
                    try:
                        if job.customer_details["email"] is not None:
                            st.write(f"- {job.customer_details['email']}")
                    except Exception:
                        logger.error(f"{job.name} does not have customer email")
                else:
                    logger.error(f"{job.name} does not have a customer linked")


def render_qty_table(form_content: dict):
    qty_list = [v for k, v in form_content["sub_lines"].items()]
    fetched_qty = pd.DataFrame.from_records(qty_list)
    fixed_items = [
        ("Install rodding eyes for QA checks", 1.0, 150.0),
    ]
    fixed_item_df = pd.DataFrame(fixed_items, columns=["line", "qty", "rate"])
    contract_table = pd.concat([fetched_qty, fixed_item_df])
    contract_table["Line Value"] = contract_table["qty"] * contract_table["rate"]
    contract_table = contract_table.loc[contract_table.qty > 0].dropna()

    st.markdown(contract_table.to_html(index=False), unsafe_allow_html=True)
    fmt1, fmt2, fmt3 = st.columns(3)
    fmt3.metric("Total Value", f"$ {contract_table['Line Value'].sum():,.2f}", "")


def render_contract_message(
    subcon: str,
    subcon_detials_df: pl.DataFrame,
    form_content: dict,
    project: Project,
):
    main_contact = (
        ss.subs_details.filter(pl.col("Business") == subcon)
        .select("Main Contact")
        .item()
    )
    """
    Takes the project, subcontractor informattion, and renders a message to subcontractors
    """

    msg_pre = f"""

Hi {main_contact},

Please find below the details for the project:
> **{form_content["project"]}** \n

To be completed *before {form_content["completed_by"]}*, The project is composed of the following items of work:

"""
    msg_start = """

Attached, please also find the project's **report** and **as-built**.

As previously agreed, for a project to be considered complete and invoice paid at the current pay cycle, signed **producer statements(PS3)** and **As-built** are required.

All terms discussed and agreed prior to work commencing, including the initial terms, apply to how this project is to be carried out.
"""
    msg_mid = f"""

{"Please leave an opening for **pipelining** as required for the work, as indicated by the attached info" if "pipelining" in form_content["tags"] else ""}

{"The job site has **contaminated soil** please dispose of the soil as required by relevant regulations" if "contaminated" in form_content["tags"] else ""}

{"If you are unclear about the **hard surface areas** (concrete, asphalt, pavers etc) that need to be removed please contact me before proceeding with the demolition." if "concrete" or "asphalt" or "pavers_not_in_concrete" or "pavers_in_concrete" in form_content["sub_qty"] else ""}
"""

    msg_end = f"""

{form_content["additional_info"]}

{"Please call me prior to going to site." if form_content["to_phone"] else ""}

We require photos of toilet and boundary connections, trench bedding, photo evidence of trench compaction as part of the works. As-builts and producer statements (PS3s) are also expected as part of the works, Please submit them when you submit your invoice. The works will not be considered completed unless we receive PS3s As-builts and the specified photos --Payments will be processed once all documents are received.

Kindly reply to this with acceptance of the contract prior to beginning works. Should you proceed with works without confirmation, you are implicitly agreeing to all the terms and rates enclosed.


\n
Many thanks,\n
{form_content["project_manager"]}

"""
    # st.info(
    # f" 👇send to below {subcon.main_contact.email}, from {subcon.legal_name}, {subcon.main_contact.phone}"
    # )
    st.markdown(msg_pre)
    render_qty_table(form_content=form_content)
    st.markdown(msg_start)
    render_contact_details(project)
    st.markdown(msg_mid)
    st.markdown(msg_end)


def main():
    titlebar()
    main_area = st.empty()
    if st.session_state["status"] is None:
        with main_area.container():
            enter_project_info(projects=projects, subs_names=subs_names)

    if st.session_state["status"] == "form_completed":
        if (
            len(st.session_state["proj"].quotes) == 0
            and len(st.session_state["proj"].variation_quotes) == 0
        ) or st.session_state["manual_input"]:
            with main_area.container():
                manual_qty_input(
                    form_content=st.session_state["form"],
                    project=st.session_state["proj"],
                    subcon=st.session_state["sub"],
                    subs_rates_df=ss.subs_rates,
                )
        else:
            with main_area.container():
                check_qty(
                    form_content=st.session_state["form"],
                    project=st.session_state["proj"],
                    subcon=st.session_state["sub"],
                    subs_rates_df=ss.subs_rates,
                )

    if st.session_state["status"] == "details_checked":
        with main_area.container():
            st.write("#### 4, 5. Cut and Paste Contract to Email")

            def back_to_qty_check():
                st.session_state["status"] = "form_completed"

            st.button("go back", on_click=back_to_qty_check())
            render_contract_message(
                subcon=ss.sub,
                form_content=st.session_state["form"],
                project=st.session_state["proj"],
                subcon_detials_df=ss.subs_details,
            )


if __name__ == "__main__":
    main()
