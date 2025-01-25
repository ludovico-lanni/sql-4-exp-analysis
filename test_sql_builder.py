from utils.sql_builder import sql_builder

def test_sql_builder():
    # Inputs for the test
    assignments_query = """
    with ass as (
        SELECT
            customer_id,
            variant,
            date_ass
        FROM assignments_sql
    )
    select * from ass
    """

    assignments_mapping = {
        "randomisation_unit_id": "customer_id",
        "variant_column": "variant",
        "date_column": "date_ass"
    }

    entry_point_query = """
    with ep as (
        SELECT
            customer_id,
            date_ep
        FROM entrypoint_sql
    )
    select * from ep
    """

    entry_point_mapping = {
        "randomisation_unit_id": "customer_id",
        "date_column": "date_ep"
    }

    fact_queries = [
        {
            "query": """
            with fact_orders as (
                SELECT
                    customer_id,
                    obs_date,
                    sum(orders) as orders_created,
                    sum(canceled_orders) as orders_cancelled
                FROM obs_sql_orders
                GROUP BY 1,2
            )
            select * from fact_orders
            """,
            "mapping": {
                "randomisation_unit_id": "customer_id",
                "date_column": "obs_date",
                "fact_columns": ["orders_created", "orders_cancelled"]
            }
        },
        {
            "query": """
            with fact_sessions as (
                SELECT
                    customer_id,
                    obs_date,
                    sum(sessions) as sessions
                FROM obs_sql_sessions
                GROUP BY 1,2
            )
            select * from fact_sessions
            """,
            "mapping": {
                "randomisation_unit_id": "customer_id",
                "date_column": "obs_date",
                "fact_columns": ["sessions"]
            }
        }
    ]

    # Generate the final query
    result_query = sql_builder(assignments_query, assignments_mapping, entry_point_query, entry_point_mapping, fact_queries)

    assert len(result_query) > 0
