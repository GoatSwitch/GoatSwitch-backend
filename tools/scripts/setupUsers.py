import os
import uuid
from azure.data.tables import TableServiceClient, TableEntity


table_connection_string = os.getenv("AZ_TABLES_CONNECTION_STRING")
print(f"Table Connection String: {table_connection_string}")

# Initialize Table Service Client
table_service_client = TableServiceClient.from_connection_string(
    conn_str=table_connection_string
)
users_table_client = table_service_client.create_table_if_not_exists(table_name="users")
companies_table_client = table_service_client.create_table_if_not_exists(
    table_name="companies"
)


def create_company(company_name, subscription_type):
    company_id = str(uuid.uuid4()).replace("-", "")
    entity = TableEntity(
        {
            "PartitionKey": "CompanyPartition",
            "RowKey": company_id,
            "CompanyName": company_name,
            "SubscriptionType": subscription_type,
        }
    )
    companies_table_client.create_entity(entity=entity)
    print(f"Created company {company_name} with ID {company_id}")
    return company_id


def get_company_id(company_name):
    entities = companies_table_client.query_entities(
        query_filter=f"CompanyName eq '{company_name}'"
    )
    for entity in entities:
        return entity["RowKey"]
    return None


def get_or_create_company(company_name: str, subscription_type="Free") -> str:
    company_id = get_company_id(company_name)
    if company_id is None:
        company_id = create_company(company_name, subscription_type)
    return company_id


def get_user_id(company_id, email):
    entities = users_table_client.query_entities(
        query_filter=f"PartitionKey eq '{company_id}' and Email eq '{email}'"
    )
    for entity in entities:
        return entity["RowKey"]
    return None


def create_user(company_id, email, role, user_id):
    entity = TableEntity(
        {"PartitionKey": company_id, "RowKey": user_id, "Email": email, "Role": role}
    )
    users_table_client.create_entity(entity=entity)
    print(f"Created user {email} with ID {user_id}")


def update_user(company_id, email, role):
    user_id = get_user_id(company_id, email)
    if user_id is None:
        print(f"User {email} not found")
        return
    entity = TableEntity(
        {"PartitionKey": company_id, "RowKey": user_id, "Email": email, "Role": role}
    )
    users_table_client.update_entity(entity=entity)
    print(f"Updated user {email} with role {role}")


def create_or_update_user(company_id, email, role, id_override=None):
    user_id = get_user_id(company_id, email)
    if user_id is None:
        user_id = id_override or str(uuid.uuid4()).replace("-", "")
        create_user(company_id, email, role, user_id)
    else:
        update_user(company_id, email, role)


def setup_customer(company_name: str, subscription_type: str, user_emails: list[str]):
    company_id = get_or_create_company(company_name, subscription_type)
    for email in user_emails:
        create_or_update_user(company_id, email, "User")


if __name__ == "__main__":
    company_name = "GoatSwitch AI Test"
    subscription_type = "Premium"
    user_emails = ["test@goatswitch.ai"]

    setup_customer(company_name, subscription_type, user_emails)
