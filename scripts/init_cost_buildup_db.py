from typing import Optional
from pydantic import HttpUrl, computed_field
from sqlmodel import Field, SQLModel, create_engine
from streamlit import secrets
from datetime import date

TURSO_DB_URL = secrets["turso"]["turso_db_url"]
TURSO_DB_TOKEN = secrets["turso"]["turso_db_token"]
dbURL = f"sqlite+{TURSO_DB_URL}?authToken={TURSO_DB_TOKEN}"

LABOUR_RATE = 50


class Measure_Unit(SQLModel, table=True):
    unit_code: str = Field(primary_key=True)
    unit_long: str = Field(max_length=50)
    unit_notes: Optional[str] = Field(default=None)


units = {
    "hr": Measure_Unit(unit_code="hr", unit_long="Hourly"),
    "ea": Measure_Unit(unit_code="ea", unit_long="Each"),
    "lm": Measure_Unit(unit_code="lm", unit_long="Metre"),
    "m2": Measure_Unit(unit_code="m2", unit_long="Square Metre"),
    "m3": Measure_Unit(unit_code="m3", unit_long="Cubic Metre"),
    "sc": Measure_Unit(
        unit_code="sc",
        unit_long="scoop",
        unit_notes="generally used in landscaping supplies",
    ),
    "L": Measure_Unit(unit_code="L", unit_long="Litre"),
    "T": Measure_Unit(unit_code="T", unit_long="Tonne"),
}


class Cost_Accounts(SQLModel, table=True):
    account_code: Optional[str] = Field(default=None, primary_key=True)
    account_name: str = Field(unique=True)
    account_description: Optional[str] = Field(default=None)
    account_notes: Optional[str] = Field(default=None)


cost_accounts = {
    "LQBS": Cost_Accounts(
        account_code="LQBS", account_name="Landscaping, Quarries and Building Supplies"
    ),
    "PVC": Cost_Accounts(account_code="PVC", account_name="PVC and Drainage Suppliers"),
    "SS": Cost_Accounts(account_code="SS", account_name="Services Subcontractors"),
    "CA": Cost_Accounts(
        account_code="CA", account_name="Concrete and Asphalt Installation"
    ),
}


class Budget_Breakdown_By_Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sales_item_code: str = Field(foreign_key="sales_items.sales_item_code")
    account_code: str = Field(foreign_key="cost_accounts.account_name")
    budget_amount: float
    last_update: Optional[date] = Field(default=None)


class Sales_Items(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sales_item_code: str = Field(max_length=50, unique=True)
    description: str
    sell_price: float
    sell_item_unit: str = Field(foreign_key="units.unit_code")
    budget_labour_hrs: Optional[float] = Field(default=None)
    budget_material_cost: Optional[float] = Field(default=None)
    last_update: Optional[date] = Field(default=None)
    xero_url: Optional[HttpUrl] = Field(default=None)
    archived: bool = Field(default=False)
    notes: Optional[str] = Field(default=None)

    @computed_field()
    @property
    def labour_cost(self) -> float:
        if self.budget_labour_hrs is None:
            return 0
        else:
            return self.budget_labour_hrs * LABOUR_RATE

    @computed_field()
    @property
    def total_cost(self):
        if self.budget_material_cost is None:
            material_cost = 0
        else:
            material_cost = self.budget_material_cost
        return self.labour_cost + material_cost


# code	name	sell price	unit	Notes	link
sales_items = {
    "Add Lab": Sales_Items(
        sales_item_code="Add Lab",
        description="Additional Labour to bucket chip in and barrow spo",
        sell_price=84.00,
        sell_item_unit="hr",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/93ce6eb3-993c-4b6f-902d-488f848b4ee2"
        ),
        last_update=date.today(),
    ),
    "AP20": Sales_Items(
        sales_item_code="AP20",
        description="Supply AP20 to site per m3",
        sell_price=215.00,
        sell_item_unit="m3",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/41b9a88c-e1e6-40c6-bc61-5c4bf7520bba"
        ),
        last_update=date.today(),
    ),
    "Asphalt": Sales_Items(
        sales_item_code="Asphalt",
        description="Remove and replace asphalt driveway per m2",
        sell_price=95.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/78e3a92f-a77c-406d-8f15-c2d5181a3e93"
        ),
        last_update=date.today(),
    ),
    "Asphalt Strip": Sales_Items(
        sales_item_code="Asphalt Strip",
        description="Asphalt strip at end of concrete driveway",
        sell_price=300.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/9d28c6e5-0749-4f30-8052-65f06b9f1a4d"
        ),
        last_update=date.today(),
    ),
    "Bark Mulch": Sales_Items(
        sales_item_code="Bark Mulch",
        description="Bark Mulch per m3",
        sell_price=350.00,
        sell_item_unit="m3",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/f6cd28dc-ea77-4bff-8e71-b15d88a01819"
        ),
        last_update=date.today(),
    ),
    "Bark Nuggets": Sales_Items(
        sales_item_code="Bark Nuggets",
        description="Bark Nuggets uplift and replace per m3",
        sell_price=350.00,
        sell_item_unit="m3",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/5f4143e0-4987-4f6f-9247-c39b866f6ded"
        ),
        last_update=date.today(),
    ),
    "Boxing": Sales_Items(
        sales_item_code="Boxing",
        description="Install boxing per m",
        sell_price=16.00,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/97e30b7f-d4f4-4b76-9ccd-64910c308362"
        ),
        last_update=date.today(),
    ),
    "Bubble Up Sump": Sales_Items(
        sales_item_code="Bubble Up Sump",
        description="Supply and install bubble up sump",
        sell_price=577.50,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/70f1d777-78de-4b61-be5b-0ea46553862f"
        ),
        last_update=date.today(),
    ),
    "Bush": Sales_Items(
        sales_item_code="Bush",
        description="Remove and dispose bush/tree",
        sell_price=367.50,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/c0af0c05-e33d-4e48-85b0-85b5c17544b0"
        ),
        last_update=date.today(),
    ),
    "Cap Sewer": Sales_Items(
        sales_item_code="Cap Sewer",
        description="Cap Drains P/M (Drain is less than 300mm deep)",
        sell_price=100.00,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/4b836c2d-5d0a-4bc2-8858-364d6b91c5f1"
        ),
        last_update=date.today(),
    ),
    "CCTV": Sales_Items(
        sales_item_code="CCTV",
        description="CCTV to check SW",
        sell_price=183.75,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/3414d9d3-4418-4fd3-924e-0b88461d0ace"
        ),
        last_update=date.today(),
    ),
    "Channel Drain": Sales_Items(
        sales_item_code="Channel Drain",
        description="Channel Drain per metre",
        sell_price=189.00,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/ad5609fd-5cb8-4e4a-b2f6-63cea6d5317f"
        ),
        last_update=date.today(),
    ),
    "Channel Min Charge": Sales_Items(
        sales_item_code="Channel Min Charge",
        description="Channel Drain Minimum Charge",
        sell_price=945.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/8829f1ca-7061-4a81-92d4-6f3759131ffc"
        ),
        last_update=date.today(),
    ),
    "Clothes Line": Sales_Items(
        sales_item_code="Clothes Line",
        description="Clothes Line remove, store on site and reinstate",
        sell_price=315.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/8829f1ca-7061-4a81-92d4-6f3759131ffc"
        ),
        last_update=date.today(),
    ),
    "CO": Sales_Items(
        sales_item_code="CO",
        description="New curb outlet",
        sell_price=2625.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/f9ed21a6-2792-4282-9755-c3d0bb771e5a"
        ),
        last_update=date.today(),
    ),
    "Coloured Concrete": Sales_Items(
        sales_item_code="Coloured Concrete",
        description="Remove and replace coloured concrete",
        sell_price=195.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/0a1b44d0-9149-4502-a55a-b5f7ae5e79b8"
        ),
        last_update=date.today(),
    ),
    "Con Kerb Min Charge": Sales_Items(
        sales_item_code="Con Kerb Min Charge",
        description="Concrete kerbing (Minimum Charge)",
        sell_price=900.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/1282c08c-81ec-49ae-ba2e-d86067fa789e"
        ),
        last_update=date.today(),
    ),
    "Conc Curb": Sales_Items(
        sales_item_code="Conc Curb",
        description="Concrete curbing per m",
        sell_price=100.00,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/1282c08c-81ec-49ae-ba2e-d86067fa789e"
        ),
        last_update=date.today(),
    ),
    "Concrete Cut": Sales_Items(
        sales_item_code="Concrete Cut",
        description="Double cut concrete P/LM (10 LM Minimum Charge)",
        sell_price=44.20,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/37d2af8b-c557-42d4-aa7b-b3fad6abad3b"
        ),
        last_update=date.today(),
    ),
    "Concrete Removal": Sales_Items(
        sales_item_code="Concrete Removal",
        description="Concrete removal per m2",
        sell_price=63.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/ddb9939f-e0a6-430b-9a15-1c4c0089a6dc"
        ),
        last_update=date.today(),
    ),
    "Conn Toilet": Sales_Items(
        sales_item_code="Conn Toilet",
        description="Cut in connection to toilet / soil stack",
        sell_price=190.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/8b6bf1d7-654d-457c-aaaf-eda49725c14f"
        ),
        last_update=date.today(),
    ),
    "Deck": Sales_Items(
        sales_item_code="Deck",
        description="Remove and replace decking per m2",
        sell_price=475.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/7fd47c14-d4b1-492f-a696-10f13946259a"
        ),
        last_update=date.today(),
    ),
    "Drive Sump": Sales_Items(
        sales_item_code="Drive Sump",
        description="Heavy duty Driveway Sump - Supply and install",
        sell_price=690.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/193c7168-8df8-43fd-84ec-c3d67b19fa01"
        ),
        last_update=date.today(),
    ),
    "Edging": Sales_Items(
        sales_item_code="Edging",
        description="Wooden Garden Edging 200mm x5m pack",
        sell_price=66.93,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/193c7168-8df8-43fd-84ec-c3d67b19fa01"
        ),
        last_update=date.today(),
    ),
    "EQC - Jet & Suck": Sales_Items(
        sales_item_code="EQC - Jet & Suck",
        description="Jet & Vacuum",
        sell_price=600.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/2864e38a-9bdb-4a95-8a5a-654550d9a413"
        ),
        last_update=date.today(),
    ),
    "exposedag": Sales_Items(
        sales_item_code="exposedag",
        description="Remove and replace exposed aggregate concrete",
        sell_price=195.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/1c18e090-4978-4510-94d7-6a84d305cd57"
        ),
        last_update=date.today(),
    ),
    "Fence": Sales_Items(
        sales_item_code="Fence",
        description="Fence - remove and reinstate fence (replace if nec",
        sell_price=273.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/cf426fa1-2cb2-4ba0-90c2-e8bfe5a3ceb3"
        ),
        last_update=date.today(),
    ),
    "Fence Min": Sales_Items(
        sales_item_code="Fence Min",
        description="Fence (Minimum charge)",
        sell_price=1235.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/c2b9ead7-38d6-47af-bf7a-13fe56458f8a"
        ),
        last_update=date.today(),
    ),
    "Gas Bottle": Sales_Items(
        sales_item_code="Gas Bottle",
        description="Gas Bottle - temporary supply. Remove large bottle",
        sell_price=105.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/c2b9ead7-38d6-47af-bf7a-13fe56458f8a"
        ),
        last_update=date.today(),
    ),
    "Gravel": Sales_Items(
        sales_item_code="Gravel",
        description="Driveway gravel to resurface driveway per m3",
        sell_price=215.00,
        sell_item_unit="m3",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/fe009d58-bae3-4a61-b598-b73cb4ea379d"
        ),
        last_update=date.today(),
    ),
    "HAIL": Sales_Items(
        sales_item_code="HAIL",
        description="Remove and dispose contaminated soil per lm",
        sell_price=90.50,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/a900fed5-0bdb-46cb-91a0-3b7e1c1d0e23"
        ),
        last_update=date.today(),
    ),
    "Hardfill": Sales_Items(
        sales_item_code="Hardfill",
        description="AP20/40 per m3 (includes delivery and compaction)",
        sell_price=215.00,
        sell_item_unit="m3",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/cd2606a7-52aa-498a-b238-243fed3a030e"
        ),
        last_update=date.today(),
    ),
    "Heatpump": Sales_Items(
        sales_item_code="Heatpump",
        description="Disconnect / reconnect heatpump",
        sell_price=475.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/0fb0975e-d9dc-4517-9ab9-49aaa8cbbe63"
        ),
        last_update=date.today(),
    ),
    "Hydro": Sales_Items(
        sales_item_code="Hydro",
        description="Supply and compact soil, level, hydroseed above tr",
        sell_price=525.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/bb85c6f8-463d-4283-90e0-ea882c102be4"
        ),
        last_update=date.today(),
    ),
    "Jet & Suck": Sales_Items(
        sales_item_code="Jet & Suck",
        description="Jetting and Vacuum clear drainage",
        sell_price=325.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/749c0297-9e4b-41d2-9af9-5296c282461d"
        ),
        last_update=date.today(),
    ),
    "Labour": Sales_Items(
        sales_item_code="Labour",
        description="standard labour hour",
        sell_price=84.00,
        sell_item_unit="hr",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/2b8e84b7-9696-42f8-9fa9-1462cb89848f"
        ),
        last_update=date.today(),
    ),
    "Minimum Asphalt": Sales_Items(
        sales_item_code="Minimum Asphalt",
        description="Minimum charge for asphalt",
        sell_price=1200.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/2b8e84b7-9696-42f8-9fa9-1462cb89848f"
        ),
        last_update=date.today(),
    ),
    "Paint": Sales_Items(
        sales_item_code="Paint",
        description="Painting or staining per m2",
        sell_price=45.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/2b8e84b7-9696-42f8-9fa9-1462cb89848f"
        ),
        last_update=date.today(),
    ),
    "Paint Min Charge": Sales_Items(
        sales_item_code="Paint Min Charge",
        description="Painting or staining minimum charge",
        sell_price=700.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/2b8e84b7-9696-42f8-9fa9-1462cb89848f"
        ),
        last_update=date.today(),
    ),
    "Pavers": Sales_Items(
        sales_item_code="Pavers",
        description="Uplift, store onsite, prepare surface and relay Pa",
        sell_price=205.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/2b8e84b7-9696-42f8-9fa9-1462cb89848f"
        ),
        last_update=date.today(),
    ),
    "Pavers - set in concrete": Sales_Items(
        sales_item_code="Pavers - set in concrete",
        description="Remove and replace pavers set in concrete per m2",
        sell_price=330.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/30b56b0a-0fd6-4f2f-9824-82e55e634345"
        ),
        last_update=date.today(),
    ),
    "Pavers in Conc Min Charge": Sales_Items(
        sales_item_code="Pavers in Conc Min Charge",
        description="Remove and replace pavers set in concrete min",
        sell_price=3000.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/30b56b0a-0fd6-4f2f-9824-82e55e634345"
        ),
        last_update=date.today(),
    ),
    "Pavers Min Charge": Sales_Items(
        sales_item_code="Pavers Min Charge",
        description="Pavers not in concrete - min charge",
        sell_price=2460.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/30b56b0a-0fd6-4f2f-9824-82e55e634345"
        ),
        last_update=date.today(),
    ),
    "Pipeline Patch": Sales_Items(
        sales_item_code="Pipeline Patch",
        description="Pipe lining patch repair up to 3m",
        sell_price=4105.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/30b56b0a-0fd6-4f2f-9824-82e55e634345"
        ),
        last_update=date.today(),
    ),
    "PLEX": Sales_Items(
        sales_item_code="PLEX",
        description="Pipelining Excavation Hole",
        sell_price=925.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/c97045e9-0f1e-4966-8f1d-5a3b3cb34685"
        ),
        last_update=date.today(),
    ),
    "Power pole HIAB": Sales_Items(
        sales_item_code="Power pole HIAB",
        description="Power pole stabilisation - HIAB per day",
        sell_price=1890.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/195dec62-6290-4994-9e37-8d2013624f78"
        ),
        last_update=date.today(),
    ),
    "PS3/AS-Built": Sales_Items(
        sales_item_code="PS3/AS-Built",
        description="CCTV, PS3 (Drainage Producer Statement) and As Bui",
        sell_price=367.50,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/c97045e9-0f1e-4966-8f1d-5a3b3cb34685"
        ),
        last_update=date.today(),
    ),
    "Pump & Alarm": Sales_Items(
        sales_item_code="Pump & Alarm",
        description="SS Pump & Alarm",
        sell_price=1247.40,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/526b90d3-7a57-458b-8b97-b3b5c362d9cd"
        ),
        last_update=date.today(),
    ),
    "PVC to EW Connector": Sales_Items(
        sales_item_code="PVC to EW Connector",
        description="PVC to Earthenware connection adapter",
        sell_price=150.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/195dec62-6290-4994-9e37-8d2013624f78"
        ),
        last_update=date.today(),
    ),
    "RCC Min Charge": Sales_Items(
        sales_item_code="RCC Min Charge",
        description="Remove and replace coloured concrete (Min Charge)",
        sell_price=2250.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/278e852e-7be6-4fd8-888a-e564c18d3927"
        ),
        last_update=date.today(),
    ),
    "RCD": Sales_Items(
        sales_item_code="RCD",
        description="Remove and replace plain concrete driveway per m2",
        sell_price=185.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/9a558f4c-98ca-432a-a711-9c30f4052ffb"
        ),
        last_update=date.today(),
    ),
    "RCD Min Charge": Sales_Items(
        sales_item_code="RCD Min Charge",
        description="Remove and replace plain concrete driveway (Min C",
        sell_price=2620.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(url=""),
        last_update=date.today(),
    ),
    "RCP": Sales_Items(
        sales_item_code="RCP",
        description="Remove and replace concrete path per m2",
        sell_price=170.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/526b90d3-7a57-458b-8b97-b3b5c362d9cd"
        ),
        last_update=date.today(),
    ),
    "RCP min charge": Sales_Items(
        sales_item_code="RCP min charge",
        description="Remove and replace concrete (Minimum charge)",
        sell_price=2100.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/2a6dc3dc-7955-4397-9281-94fb610e0f44"
        ),
        last_update=date.today(),
    ),
    "RCS": Sales_Items(
        sales_item_code="RCS",
        description="Remove and replace Stamped Concrete per m2",
        sell_price=235.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/443a2755-1613-4a61-86c9-1d65df5144e6"
        ),
        last_update=date.today(),
    ),
    "Ready Lawn": Sales_Items(
        sales_item_code="Ready Lawn",
        description="Ready Lawn per m2",
        sell_price=49.50,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/de1e7e35-2bf7-4ed9-b3de-9c948519b5b5"
        ),
        last_update=date.today(),
    ),
    "Ready Lawn Min Charge": Sales_Items(
        sales_item_code="Ready Lawn Min Charge",
        description="Ready lawn minimum charge",
        sell_price=850.00,
        sell_item_unit="ea",
        last_update=date.today(),
    ),
    "Ready Lawn Prep": Sales_Items(
        sales_item_code="Ready Lawn Prep",
        description="Screened soil, labour prep for Ready Lawn per 10m2",
        sell_price=350.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/278e852e-7be6-4fd8-888a-e564c18d3927"
        ),
        last_update=date.today(),
        archived=True,
    ),
    "Reo": Sales_Items(
        sales_item_code="Reo",
        description="Install reinforcing steel in concrete per m2",
        sell_price=25.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/efe0fd7b-1a98-4a83-b31b-59c55230d9a7"
        ),
        last_update=date.today(),
    ),
    "Reo Min Charge": Sales_Items(
        sales_item_code="Reo Min Charge",
        description="Reinforcing steel in concrete (Minimum charge)",
        sell_price=500.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/efe0fd7b-1a98-4a83-b31b-59c55230d9a7"
        ),
        last_update=date.today(),
    ),
    "RGT": Sales_Items(
        sales_item_code="RGT",
        description="Remove and dispose existing gully. Supply and inst",
        sell_price=370.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/a96b2f73-8513-484d-a724-aa5b90da334c"
        ),
        last_update=date.today(),
    ),
    "SE": Sales_Items(
        sales_item_code="SE",
        description="Site Establishment",
        sell_price=750.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/1e167cbe-7a58-42a5-a2cd-095c39b3bec4"
        ),
        last_update=date.today(),
    ),
    "SEW": Sales_Items(
        sales_item_code="SEW",
        description="Remove and replace sewer per metre",
        sell_price=205.00,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/74dfe210-65a3-49f3-8b88-acf65a952145"
        ),
        last_update=date.today(),
    ),
    "SL": Sales_Items(
        sales_item_code="SL",
        description="Service Location",
        sell_price=240.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/e6ff9e2d-4a28-44be-aa38-b4126ddfa460"
        ),
        last_update=date.today(),
    ),
    "SL Selywn/Waimak": Sales_Items(
        sales_item_code="SL Selywn/Waimak",
        description="Service Location",
        sell_price=355.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/f5d3dfae-3623-4618-991f-15af55e1d5f5"
        ),
        last_update=date.today(),
    ),
    "Small": Sales_Items(
        sales_item_code="Small",
        description="Small job delivery fee",
        sell_price=685.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/1f857aef-7b1a-4dae-9f28-d202b7914373"
        ),
        last_update=date.today(),
    ),
    "Spoil Out": Sales_Items(
        sales_item_code="Spoil Out",
        description="Spoil Out - includes truck and dumping fees",
        sell_price=892.50,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/4e9fb2af-c82b-4c25-bd52-8e08b3999e8c"
        ),
        last_update=date.today(),
    ),
    "Spoil": Sales_Items(
        sales_item_code="Spoil",
        description="Spoil WDC",
        sell_price=1392.50,
        sell_item_unit="ea",
        last_update=date.today(),
    ),
    "SSSW": Sales_Items(
        sales_item_code="SSSW",
        description="Remove and replace sewer and stormwater. Shared tr",
        sell_price=265.00,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/2126cf83-76e1-478b-b22b-23ba0d17bde2"
        ),
        last_update=date.today(),
    ),
    "Stamped Concrete": Sales_Items(
        sales_item_code="Stamped Concrete",
        description="Remove and replace Stamped Concrete per m2",
        sell_price=235.00,
        sell_item_unit="m2",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/443a2755-1613-4a61-86c9-1d65df5144e6"
        ),
        last_update=date.today(),
        notes="updated price",
    ),
    "Steps": Sales_Items(
        sales_item_code="Steps",
        description="Concrete steps",
        sell_price=1000.00,
        sell_item_unit="ea",
        last_update=date.today(),
    ),
    "Stone": Sales_Items(
        sales_item_code="Stone",
        description="Decorative stone to remove and replace per m3",
        sell_price=215.00,
        sell_item_unit="m3",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/1044f378-70a5-4400-a3d6-19301f5aac9d"
        ),
        last_update=date.today(),
    ),
    "Stone on Mat": Sales_Items(
        sales_item_code="Stone on Mat",
        description="Uplift, store, reinstate decorative stones on matt",
        sell_price=45.00,
        sell_item_unit="ea",
        last_update=date.today(),
    ),
    "Stump": Sales_Items(
        sales_item_code="Stump",
        description="Remove and dispose tree, includes root and stump g",
        sell_price=1365.00,
        sell_item_unit="ea",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/657b9bb8-4d0b-4d7c-8346-339dd54db97c"
        ),
        last_update=date.today(),
    ),
    "SW": Sales_Items(
        sales_item_code="SW",
        description="Remove and replace stormwater per m",
        sell_price=175.00,
        sell_item_unit="lm",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/de824b3f-cf66-4e40-bd06-16f0d01fc210"
        ),
        last_update=date.today(),
    ),
    "Tailings": Sales_Items(
        sales_item_code="Tailings",
        description="Tailings (stones) to remove and replace per m3",
        sell_price=75.60,
        sell_item_unit="m3",
        xero_url=HttpUrl(
            url="https://go.xero.com/app/!VkWjW/products-and-services/9d28c6e5-0749-4f30-8052-65f06b9f1a4d"
        ),
        last_update=date.today(),
        notes="prices guessed from retail price",
    ),
    "Term Vent": Sales_Items(
        sales_item_code="Term Vent",
        description="Remove and dispose existing terminal vent connecti",
        sell_price=800.00,
        sell_item_unit="ea",
        last_update=date.today(),
    ),
    "Tree": Sales_Items(
        sales_item_code="Tree",
        description="Tree removal and green waste disposal",
        sell_price=1050.00,
        sell_item_unit="ea",
        last_update=date.today(),
    ),
    "Trench Shield": Sales_Items(
        sales_item_code="Trench Shield",
        description="Manhole Trench Shield",
        sell_price=1050.00,
        sell_item_unit="ea",
        last_update=date.today(),
    ),
    "Watermain": Sales_Items(
        sales_item_code="Watermain",
        description="Install new 25mm Blueline in existing trench per m",
        sell_price=25.00,
        sell_item_unit="lm",
        last_update=date.today(),
    ),
    "Weed Mat": Sales_Items(
        sales_item_code="Weed Mat",
        description="Weed mat 1m x 20m (Minimum charge)",
        sell_price=150.00,
        sell_item_unit="ea",
        last_update=date.today(),
    ),
    "Unblock": Sales_Items(
        sales_item_code="Unblock",
        description="Unblock Drains",
        sell_price=236.25,
        sell_item_unit="ea",
        last_update=date.today(),
        notes="No buildup, just added a random cost, archived code",
        archived=True,
    ),
    "COM": Sales_Items(
        sales_item_code="COM",
        description="Compactor per day",
        sell_price=105.00,
        sell_item_unit="ea",
        last_update=date.today(),
        notes="no buildup, just added  retainl hire rate",
    ),
    "Survey": Sales_Items(
        sales_item_code="Survey",
        description="Survey",
        sell_price=1500.00,
        sell_item_unit="ea",
        last_update=date.today(),
        notes="blank code,  to get around errors",
    ),
    "Survey Cost": Sales_Items(
        sales_item_code="Survey Cost",
        description="Drainage Survey Cost Per Hour",
        sell_price=180.00,
        sell_item_unit="hr",
        last_update=date.today(),
        notes="just using base labour rate",
    ),
    "Shed": Sales_Items(
        sales_item_code="Shed",
        description="empty standin for random shed lines",
        sell_price=1500.00,
        sell_item_unit="ea",
        last_update=date.today(),
        notes="blank code,  to get around errors",
    ),
}


class Buildup_Steps(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sales_item_code: str = Field(foreign_key="units.unit_code")
    step_description: str
    step_order: int  # order of the step in the build up, default to 10 per step order, 20, 30, 40 etc. so when inserting a new step, it can be inserted between existing steps
    labour_hours: Optional[float] = Field(default=None)
    labour_costs: Optional[float] = Field(default=None)
    material_supplier_desc: Optional[str] = Field(default=None)
    material_unit: Optional[str] = Field(default=None, foreign_key="units.unit_code")
    material_supplier_unit_cost: Optional[float] = Field(default=None)
    material_qty: Optional[float] = Field(default=None)
    cost_account: Optional[str] = Field(
        default=None, foreign_key="cost_accounts.account_name"
    )
    last_update: Optional[date] = Field(default=None)
    line_note: Optional[str] = Field(default=None)
    material_cost: Optional[float] = Field(default=None)


building_steps = {
    "add_lab": {
        1: Buildup_Steps(
            sales_item_code=units["hr"].unit_code,
            step_description="Labour charged per hour",
            step_order=10,
            labour_hours=1,
            labour_costs=LABOUR_RATE * 1,
            last_update=date.today(),
        ),
    }
}


class Pricing(SQLModel, table=True):
    item_code: str = Field(default=None, primary_key=True)
    item_name: str
    share_pct: float
    source_item: str = Field(foreign_key="sales_items.sales_item_code")


def build_intial_db():
    """Build initial database structure."""
    pass


if __name__ == "__main__":
    engine = create_engine(dbURL, connect_args={"check_same_thread": False}, echo=True)
    SQLModel.metadata.create_all(engine)
