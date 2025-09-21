# routers/samples.py - Sample Data Router
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

# Sample AS/400 data for testing and demonstration
SAMPLE_DATA = {
    "customer": {
        "description": "AS/400 Customer Master File (CUSTMST)",
        "data": """CUSTNO,CUSTNAME,ADDR1,ADDR2,CITY,STATE,ZIP,PHONE,SALESREP,CREDITLMT,BALANCE
001234,ACME CORPORATION,123 MAIN ST,,CHICAGO,IL,60601,3125551234,REP001,50000.00,25000.00
002345,GLOBAL SYSTEMS INC,456 OAK AVE,SUITE 100,NEW YORK,NY,10001,2125555678,REP002,75000.00,35000.00
003456,TECH SOLUTIONS LLC,789 PINE RD,,LOS ANGELES,CA,90210,3235559876,REP003,100000.00,45000.00
004567,MANUFACTURING CO,321 ELM ST,BUILDING B,DETROIT,MI,48201,3135554321,REP001,200000.00,75000.00
005678,RETAIL PARTNERS,654 MAPLE AVE,,ATLANTA,GA,30301,4045556789,REP004,150000.00,60000.00""",
        "columns": ["CUSTNO", "CUSTNAME", "ADDR1", "ADDR2", "CITY", "STATE", "ZIP", "PHONE", "SALESREP", "CREDITLMT", "BALANCE"],
        "record_count": 5,
        "typical_use": "Customer management, billing, sales analysis"
    },
    "employee": {
        "description": "AS/400 Employee Payroll Data (PAYROLL)",
        "data": """EMPNO,EMPNAME,DEPT,JOBTITLE,HIREDATE,SALARY,BONUS,TAXCODE,SSN,STATUS
E001,JOHN SMITH,ACCT,ACCOUNTANT,19951015,45000.00,2000.00,A,123456789,A
E002,JANE DOE,ENGR,ENGINEER,20000301,55000.00,5000.00,B,234567890,A
E003,BOB JOHNSON,SALES,SALES REP,19981120,40000.00,3000.00,A,345678901,A
E004,ALICE BROWN,MGMT,MANAGER,19921201,75000.00,10000.00,C,456789012,A
E005,CHARLIE DAVIS,IT,DEVELOPER,20050615,60000.00,4000.00,B,567890123,A""",
        "columns": ["EMPNO", "EMPNAME", "DEPT", "JOBTITLE", "HIREDATE", "SALARY", "BONUS", "TAXCODE", "SSN", "STATUS"],
        "record_count": 5,
        "typical_use": "Payroll processing, HR management, reporting"
    },
    "inventory": {
        "description": "AS/400 Inventory Records (INVMST)",
        "data": """PARTNO,PARTDESC,QTY,UNITPRICE,LOCATION,VENDOR,LASTORDER,REORDERLVL,CATEGORY
P1001,WIDGET TYPE A,150,12.50,WH01,VENDOR001,20231201,25,WIDGETS
P1002,GADGET BLUE,75,25.99,WH02,VENDOR002,20231215,10,GADGETS
P1003,COMPONENT X1,200,5.75,WH01,VENDOR001,20231210,50,COMPONENTS
P1004,ASSEMBLY KIT,45,89.99,WH03,VENDOR003,20231205,15,ASSEMBLIES
P1005,SPARE PART Y2,300,3.25,WH01,VENDOR001,20231218,100,SPARES""",
        "columns": ["PARTNO", "PARTDESC", "QTY", "UNITPRICE", "LOCATION", "VENDOR", "LASTORDER", "REORDERLVL", "CATEGORY"],
        "record_count": 5,
        "typical_use": "Inventory management, procurement, stock control"
    },
    "transactions": {
        "description": "AS/400 Financial Transactions (TRANLOG)",
        "data": """TRANID,ACCTNO,TRANDATE,AMOUNT,TRANTYPE,DESCRIPTION,REFNO,CUSTNO,EMPNO
T001,1001,20240101,1500.00,CR,DEPOSIT,DEP001,001234,E001
T002,1001,20240102,-250.00,DB,WITHDRAWAL,WD001,001234,E001
T003,1002,20240103,2000.00,CR,PAYMENT RECEIVED,PAY001,002345,E002
T004,1003,20240104,-750.00,DB,SERVICE CHARGE,SC001,003456,E003
T005,1001,20240105,500.00,CR,INTEREST PAYMENT,INT001,001234,E001""",
        "columns": ["TRANID", "ACCTNO", "TRANDATE", "AMOUNT", "TRANTYPE", "DESCRIPTION", "REFNO", "CUSTNO", "EMPNO"],
        "record_count": 5,
        "typical_use": "Financial reporting, audit trails, transaction processing"
    },
    "orders": {
        "description": "AS/400 Sales Orders (ORDMST)",
        "data": """ORDERNO,CUSTNO,ORDERDT,SHIPDT,SALESREP,ITEMNO,QTY,UNITPRICE,TOTAL,STATUS
O001,001234,20240115,20240118,REP001,P1001,10,12.50,125.00,SHIPPED
O002,002345,20240116,20240119,REP002,P1002,5,25.99,129.95,SHIPPED
O003,003456,20240117,,REP003,P1003,20,5.75,115.00,PENDING
O004,001234,20240118,20240121,REP001,P1004,2,89.99,179.98,SHIPPED
O005,004567,20240119,,REP001,P1005,50,3.25,162.50,PROCESSING""",
        "columns": ["ORDERNO", "CUSTNO", "ORDERDT", "SHIPDT", "SALESREP", "ITEMNO", "QTY", "UNITPRICE", "TOTAL", "STATUS"],
        "record_count": 5,
        "typical_use": "Order processing, sales tracking, fulfillment"
    },
    "vendors": {
        "description": "AS/400 Vendor Master (VENDMST)",
        "data": """VENDORNO,VENDORNAME,CONTACT,PHONE,EMAIL,ADDR1,CITY,STATE,ZIP,PAYTERMS,STATUS
VENDOR001,ACME SUPPLIES INC,JOHN ADAMS,5551234567,jadams@acmesupplies.com,100 SUPPLY ST,BOSTON,MA,02101,NET30,ACTIVE
VENDOR002,TECH COMPONENTS LLC,SARAH JONES,5552345678,sjones@techcomp.com,200 TECH BLVD,AUSTIN,TX,73301,NET15,ACTIVE
VENDOR003,GLOBAL MANUFACTURING,MIKE CHEN,5553456789,mchen@globalmfg.com,300 FACTORY RD,DETROIT,MI,48201,NET45,ACTIVE
VENDOR004,OFFICE SOLUTIONS,LISA TAYLOR,5554567890,ltaylor@officesol.com,400 BUSINESS WAY,DENVER,CO,80201,NET30,INACTIVE
VENDOR005,SHIPPING PARTNERS,TOM WILSON,5555678901,twilson@shippartners.com,500 LOGISTICS DR,ATLANTA,GA,30301,COD,ACTIVE""",
        "columns": ["VENDORNO", "VENDORNAME", "CONTACT", "PHONE", "EMAIL", "ADDR1", "CITY", "STATE", "ZIP", "PAYTERMS", "STATUS"],
        "record_count": 5,
        "typical_use": "Vendor management, procurement, accounts payable"
    }
}

@router.get("/sample-data")
async def list_sample_data():
    """List all available sample data types"""
    return {
        "available_samples": list(SAMPLE_DATA.keys()),
        "total_samples": len(SAMPLE_DATA),
        "description": "AS/400 legacy system sample data for testing modernization"
    }

@router.get("/sample-data/{data_type}")
async def get_sample_data(data_type: str) -> Dict[str, Any]:
    """Get sample AS/400 data for testing"""
    if data_type not in SAMPLE_DATA:
        raise HTTPException(
            status_code=404, 
            detail=f"Sample data type '{data_type}' not found. Available types: {list(SAMPLE_DATA.keys())}"
        )
    
    return SAMPLE_DATA[data_type]

@router.get("/sample-data/{data_type}/metadata")
async def get_sample_metadata(data_type: str):
    """Get metadata about sample data"""
    if data_type not in SAMPLE_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"Sample data type '{data_type}' not found"
        )
    
    sample = SAMPLE_DATA[data_type]
    
    return {
        "data_type": data_type,
        "description": sample["description"],
        "columns": sample["columns"],
        "record_count": sample["record_count"],
        "typical_use": sample["typical_use"],
        "modernization_benefits": [
            "Convert legacy column names to modern snake_case format",
            "Add proper data types and constraints",
            "Generate REST API endpoints",
            "Create microservices architecture",
            "Implement data validation rules"
        ]
    }