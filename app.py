import streamlit as st
import sqlparse
from utils.sql_builder import sql_builder

def main():
    st.title("SQL Query Builder x Experiment Analysis")

    st.markdown("""
    Use this app to input individual SQL queries for assignments, entry points and facts, 
    and generate the final SQL query that will aggregate the experimental data at randomisation unit level.
    
    The generator will handle the joins and aggregations for you, so you can focus on the analysis later on. 
    Once the query is generated, you can copy it to the clipboard, paste it and run it in your query engine.
    
    Such a dataset can be analysed straight away in a Jupyter notebook or any other data analysis tool. 
    Because all facts are aggregated at the randomisation unit level, we recommend using the t-test for simple metrics 
    and pair it with the delta method for ratio metrics.
    """)

    st.markdown("## Input the SQL Components")

    st.markdown("""
    For the generator to work properly, we recommend using the following format for your SQL queries:
    - Use CTEs to structure your queries. Even if it's a single SELECT statement, wrap it in a CTE.
    - the final SELECT statement should be the last statement in the query, and should be 
    `select * from <final_cte_name>`
    - don't use semicolons at the end of each statement
    """)

    # Input fields for assignment SQL query
    st.markdown("### Assignments SQL Query")
    st.markdown("""
    The query should return the randomisation unit ID, the variant column and the date column for the first assignment 
    of that unit.
    """)
    assignments_sql = st.text_area("Enter the Assignments SQL query (write here):")
    st.code(assignments_sql, language='sql')
    assignments_mapping = {
        "randomisation_unit_id": st.text_input("Map column name for randomisation_unit_id (Assignments):"),
        "variant_column": st.text_input("Map column name for variant_column (Assignments):"),
        "date_column": st.text_input("Map column name for date_column (Assignments):")
    }

    # Input fields for entry point SQL query
    st.markdown("### Entry Point SQL Query")
    st.markdown("""
        The query should return the randomisation unit ID and the date column for each entry point.
        """)
    entry_point_sql = st.text_area("Enter the Entry Point SQL query (write here):")
    st.code(entry_point_sql, language='sql')
    entry_point_mapping = {
        "randomisation_unit_id": st.text_input("Map column name for randomisation_unit_id (Entry Point):"),
        "date_column": st.text_input("Map column name for date_column (Entry Point):")
    }

    # Input fields for fact SQL queries
    st.markdown("### Fact SQL Queries")
    st.markdown("""
        Each fact SQL query should return the randomisation unit ID, the date column and the fact columns for each fact.
        Hence, the level of aggregation must be at the (randomisation unit + date) level.
        """)
    fact_queries = []
    fact_count = st.number_input("How many Fact SQL queries do you want to input?", min_value=1, step=1)

    for i in range(fact_count):
        st.markdown(f"#### Fact SQL Query {i + 1}")
        fact_sql = st.text_area(f"Enter Fact SQL Query {i + 1} (write here):", key=f"fact_sql_{i}")
        st.code(fact_sql, language='sql')
        fact_mapping = {
            "randomisation_unit_id": st.text_input(f"Map column name for randomisation_unit_id (Fact {i + 1}):", key=f"fact_ru_{i}"),
            "date_column": st.text_input(f"Map column name for date_column (Fact {i + 1}):", key=f"fact_date_{i}"),
            "fact_columns": st.text_input(f"Map column names for fact_columns (comma-separated) (Fact {i + 1}):", key=f"fact_cols_{i}").split(",")
        }
        fact_queries.append({"query": fact_sql, "mapping": fact_mapping})

    st.markdown("## Generate the Final SQL Query")

    # Generate SQL button
    if st.button("Generate Final SQL Query"):
        try:
            final_sql = sql_builder(assignments_sql, assignments_mapping, entry_point_sql, entry_point_mapping, fact_queries)
            # Beautify the SQL query
            formatted_sql = sqlparse.format(final_sql, reindent=True, keyword_case='upper')
            st.success("Final SQL Query Generated Successfully!")

            # Display the generated SQL as a code block
            st.code(formatted_sql, language='sql')

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
