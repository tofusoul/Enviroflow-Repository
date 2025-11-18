from .job import DEFAULT_QTY_FROM_CARD, Job, build_job_from_job_card_dict
from .labour_records import Labour_Records
from .project import Project, Raw_Project
from .quote import Quote, merge_quotes as merge_quotes
from .sales_items import Sales_Item, build_sales_items_from_tables

# Person, Customer, Customers,Quote, Quotes, Subcontractor, Subcontractors, Concrete_Type, Job, Jobs, Booking_Status, Project, Projects, Model

if __name__ == "__main__":
    help(Job)
    print(DEFAULT_QTY_FROM_CARD)
    help(Raw_Project)
    help(Project)
    help(Quote)
    help(Labour_Records)
    help(Sales_Item)
    help(build_sales_items_from_tables)
    help(build_job_from_job_card_dict)
