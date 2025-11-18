---
title: "Enviroflow App - Rough Plan"
author: "Andrew Shih"
---

# Enviroflow App Roadmap
## V0.1 - Initial Stable State

- Initial stable version delivering some basic functionality including:
  - fetch, clean and consolidate data into a queryable database for analysis
  - basic interface for low hanging fruit features like:
    - generating the edited job scope list for the subcontractors
    - get a list of what subcontractor quantities are needed for the upcoming job
  - test the robustness of the database on the basis of the small apps
- Update Xero with simpro quotes
- Update Trello with quote quantities
- Update Xero with trello contacts
### Goals - Prioritised
- Analyse, clean and combine the data sets from separate sources.
  - [x] Create stable ways to get structured data from all relevant data sources
    - [x] Simpro
      - [x] Get everything we need out of simpro
    - [x] Xero
      - [x] List of all quotes
        - [x] Fetch quotes
        - [x] Parse quotes
      - [ ] Ways fetch updated quotes from Xero
        - [ ] fetch updated quotes
    - [x] Trello
      - [x] Fetch Trello Cards
  - [x] Get everything into typed data tables
  - [x] Get everything into a database
- [ ] CANCELLED Update Xero with quote contents from Simpro
  - [ ] CANCELLED figure out and create checks for pushing the simpro quotes up


- [x] Get the Simpro info into Xero
- [ ] CANCELLED Get Xero info into Trello
- [ ] CANCELLED Get Trello Contacts into Xero
### Milestone, MVPs
- [x] Extract Simpro data
  - [x] Simpro Quotes from PDF
  - [x] Simpro quote scrape status
  - [x] Simpro Quote Status
  - [x] Job Status in Simpro
  - [x] Quote Activities
  - [x] Invoices from Simpro
  - [x] Simpro Xero log
  - [x] Simpro Customers
  - [x] Notes and update relevant to Simpro Info
  - [x] Uninvoiced Jobs
  - [x] Simpro Invoices
  - [x] Get data typed and queryable
- [x] Extract Xero data
  - [x] Oauth flow to access Xero Api
  - [x] fetch and parse quote data
  - [x] Organise the updates to the list of quotes so the output makes sense
  - [x] make some interfaces to organise fetching data
- [x] Extract Trello data
  - [x] Fetch and parse Trello cards
- [x] Make some interfaces for tasks
  - [x] Generate the scope lists for subcontractors
  - [x] get a list of what subcontractor quantities are needed for the upcoming job
- Flask server
  - [x] Basic interface data
    - [x] Quotes
    - [ ] Cost Journals
    - [ ] Invoices
- Jupyter notebook prototypes for the Enviroflow App
  - [x] Generate scope lists for subcontractors
  - [ ] Get a list of what subcontractor quantities are needed for the upcoming job
    - [ ] Pipe-lining
    - [ ] Concrete
    - [ ] Hydro-seed
    - [ ] Asphalt
    - [ ] Heatpump
    - [ ] Fence
    - [ ] Deck

#### Dataflow
```mermaid
graph LR
    x[/Xero/]
    t[/Trello/]
    sp[/Simpro Data/]
    ps[Python Server]
    sl[Streamlit <br/> scripts]
    nb[Jupyter Notebooks]
    dl[(Google Drive<br/> Datalake)]
    tu[Trello Update <br/> Script]
    x --> ps
    ps --> nb
    t --> nb
    sp --> nb
    nb --> dl
    dl --> nb
    dl --> sl
    dl --> ps
    ps --> x
    tu --> t
    dl --> tu
    nb --> sl
```

## V0.2
### Goal (MVP)

- Create some simple interactivity and reports on the data.
- One way sync the Xero data into the Trello boards

#### Dataflow
```mermaid
graph LR
    ps([Python Server])-->dl[(Google Drive<br/> Datalake)]
    dl --> ps
    x[Xero]--> ps
    ps --> x
    t[Trello] --> ps
    sl[Streamlit <br/> script] --> dl
    dl --> sl
    sl --> t
    sp[\Simpro\] --> dl


```
#### Python Server
- Simple flask server
  - in the future will serve up a json api
  - right now it will just destructure the fetched data and generate the data frames we need and save it as CSV
- Handles the o-auth flow with xero's API
- Grabs the needed data from xero and saves it as dataframes
- Grabs the data from Trello and saves it as dataframes
##### Classes on the python server
```mermaid
classDiagram
    class Xero_Quote {
            source_dict: dict
            quote_id: str
            quote_number : str
            quote_ref: str
            quote_contact_id: str
            quote_contact_name: str
            quote_contact_email: str
            quote_status : str
            quote_created: datetime
            quote_updated: datetime
            quote_total_ex_tax: str
            quote_lines_dict: dict
            quote_lines_df: pd.core.frame.DataFrame
            quote_lines_df_human: pd.core.frame.DataFrame
            error_list: list
            get_quote_info(Xero_Quote) -> dict
    }

    class Xero_Quotes_List{


    }
    class XeroQuoteLookup {
        quote_list: list
        quote_list_df: pd.core.frame.DataFrame
        quote_list_df_human: pd.core.frame.DataFrame
        error_list: list
        read_single_quote(dict) -> Xero_Quote
        read_quotes_list(dict) -> Xero_Quotes_List
        read_multiple_quotes(dict) -> Xero_Quotes_List
    }

    class XeroContacts {

    }
    class XeroInvoices {

    }
    class XeroCosts {

    }

    ScrapedSimproQuote
    Simpro_Final_State
    SimproContacts
    Trello_Board *-- Trello_List
    Trello_List *-- Trello_Card
    Trello_Card *-- Trello_Contacts

```

#### Google Drive Datalake
- Collection of tabular data that is saved to Google Drive
#### Observable Scripts
- Collection of observable hq scripts written in 'kind of' javascript
- can be exported into executable code.
- [duckdb on observable](https://observablehq.com/@cmudig/duckdb)


### Limitations
this design means that the front end and back end users can't simultaniously be accessing the data lake at the same time, it will mean overwriting the pool of data, but that isn't too hard to manage at the moment as there is only one back end user.

should write something to prevent this from happening

## V0.2
### Goal (MVP)
- structure things so we can rapidly prototype and itterate what we do


#### Dataflow
```mermaid
graph LR
    ps([Python Server])-->dl[(Google Drive<br/> Datalake)]
    dl --> ps
    x[Xero]--> ps
    ps --> x
    t[Trello] --> ps
    o[Observable <br/> script] --> dl
    dl --> o
    o --> f
    f[Float <br/> Schedueling ] --> ps
    o --> t
```
#### Classes on the python server
```mermaid
classDiagram
    XeroQuote
    XeroContacts
    XeroInvoices
    SimproQuote
    SimproContacts
    Trello_Board *-- Trello_List
    Trello_List *-- Trello_Card
    Trello_Card *-- Trello_Contacts

```

#### Backend Sequence

```mermaid
sequenceDiagram
    participant bu as backend user
    participant t as Trello
    participant x as Xero
    participant ps as Python <br/> Server
    participant dl as Google drive <br/> Data Lake
    bu ->> ps : Starts Python Server
    activate ps
    ps ->> ps: generates a log dataframe <br/> for the session
    ps->> x  : Authentication <br/> reuqests
    Note left of ps : Simplification of <br/> xerooauth flow
    x -->>ps : Authentication <br/> response
    ps->> x  : API requests <br/> to get <br/> data from Xero
    x -->>ps : API response <br/> with data from Xero
    ps->> t  : API requests <br/> to get <br/> data from Trello
    t -->> ps  : API response <br/> with data from Trello
    ps ->> ps : unwrapping recieved <br/> json data to put <br />into pandas dataframes
    dl ->> ps : fetch CSV data from <br/> data lake
    ps->> ps : Compares <br/> data sets <br/> for the difference
    ps->> ps : update session log <br/> a report <br/> on the data
    ps-->> bu : shows difference to <br/> user
    deactivate ps
    bu->> ps  : confirms or <br/> edit then confirms <br/>the change data
    activate ps
    ps->> t  : update Trello <br/> with change data
    t -->> ps  : response with success or error
    ps->> x : update Xero <br/> with relevant data
    Note right of x : may or maynot impliment this with this version <br/>
    x -->> ps : response with success or error
    bu ->> ps : tries to close app
    ps ->> ps : append the session log <br/> results to log df <br/> fetched to data lake
    ps -->> bu : shows the log to append to log dataframe <br/> and asks for confirmation
    bu->> ps : confirms exit
    deactivate ps

```
#### Frontend Sequence

```mermaid
sequenceDiagram
    participant bu as Backend User
    participant ps as Python <br/> Server
    participant dl as Google drive <br/> Data Lake
    participant oc as observable <br/> client
    participant fu as Frontend User
    activate ps
    bu ->> ps : saves changes <br/> and extis server
    ps ->> dl : save dataframe <br/> as csv on <br/> google drive
    dl -->> ps : response with success or error <br/> and server exists
    deactivate ps
    fu ->> oc : opens observable <br/> client
        activate oc
        dl ->>  oc : Observable client <br/> fetches data from google <br/> drive via integration
        oc -->> fu : renders view of the data
    loop user interacts with data
        fu ->> oc : user interacts with data <br/> without modifying it
        oc -->> fu : renders updated view of data
        fu ->> oc : inputes and changes data
        oc ->> oc : updates data
        oc-->> fu : renders updated view of data
        oc -->> dl : update datalake <br/> with altered data
        fu ->> oc: press the save button
        oc -->> dl : save data <br/> updated data as csv on <br/> google drive
    end
        deactivate oc
    bu ->> ps : starts the server
    activate ps
    dl -->> ps : feed current data <br/> to python sever
    deactivate ps

```
