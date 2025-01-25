import streamlit as st
from utils.sql_builder import sql_builder
import pyperclip

def main():
    st.title("SQL Query Builder")

    st.markdown("""
    Use this app to input SQL queries and generate the final SQL query. Once the query is generated, you can copy it to the clipboard.
    """)

    st.subheader("Input the SQL Components")

    # Input fields for assignment SQL query
    st.markdown("### Assignments SQL Query")
    assignments_sql = st.text_area("Enter the Assignments SQL query:")
    assignments_mapping = {
        "randomisation_unit_id": st.text_input("Map column name for randomisation_unit_id (Assignments):"),
        "variant_column": st.text_input("Map column name for variant_column (Assignments):"),
        "date_column": st.text_input("Map column name for date_column (Assignments):")
    }

    # Input fields for entry point SQL query
    st.markdown("### Entry Point SQL Query")
    entry_point_sql = st.text_area("Enter the Entry Point SQL query:")
    entry_point_mapping = {
        "randomisation_unit_id": st.text_input("Map column name for randomisation_unit_id (Entry Point):"),
        "date_column": st.text_input("Map column name for date_column (Entry Point):")
    }

    # Input fields for fact SQL queries
    st.markdown("### Fact SQL Queries")
    fact_queries = []
    fact_count = st.number_input("How many Fact SQL queries do you want to input?", min_value=1, step=1)

    for i in range(fact_count):
        st.markdown(f"#### Fact SQL Query {i + 1}")
        fact_sql = st.text_area(f"Enter Fact SQL Query {i + 1}:", key=f"fact_sql_{i}")
        fact_mapping = {
            "randomisation_unit_id": st.text_input(f"Map column name for randomisation_unit_id (Fact {i + 1}):", key=f"fact_ru_{i}"),
            "date_column": st.text_input(f"Map column name for date_column (Fact {i + 1}):", key=f"fact_date_{i}"),
            "fact_columns": st.text_input(f"Map column names for fact_columns (comma-separated) (Fact {i + 1}):", key=f"fact_cols_{i}").split(",")
        }
        fact_queries.append({"query":fact_sql, "mapping": fact_mapping})

    # Generate SQL button
    if st.button("Generate Final SQL Query"):
        try:
            final_sql = sql_builder(assignments_sql, assignments_mapping, entry_point_sql, entry_point_mapping, fact_queries)
            st.success("Final SQL Query Generated Successfully!")

            # Display the generated SQL
            st.text_area("Final SQL Query:", final_sql, height=300)

            # Copy to clipboard button
            if st.button("Copy to Clipboard"):
                pyperclip.copy(final_sql)
                st.info("SQL query copied to clipboard!")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()