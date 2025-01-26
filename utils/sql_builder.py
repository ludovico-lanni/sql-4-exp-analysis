def sql_builder(assignments_query, assignments_mapping, entry_point_query, entry_point_mapping, fact_queries):
    """
    Builds the final SQL query from user-provided input, avoiding nested WITH statements.

    :param assignments_query: The SQL query for assignments data.
    :param assignments_mapping: A dictionary mapping column names in assignments_query to
                                'randomisation_unit_id', 'variant_column', and 'date_column'.
    :param entry_point_query: The SQL query for entry points data.
    :param entry_point_mapping: A dictionary mapping column names in entry_point_query to
                                'randomisation_unit_id' and 'date_column'.
    :param fact_queries: A list of dictionaries. Each dictionary contains a 'query' key for the fact SQL query
                         and a 'mapping' key mapping column names in the query to
                         'randomisation_unit_id', 'date_column', and 'fact_columns' (list of columns).
    :return: A string containing the final SQL query.
    """

    def process_query(sql):
        """
        Converts the input SQL query into a reshaped SQL code block so that:
        - the starting WITH word is removed
        - the final SELECT statement is completely removed
        Additionally, returns the name of the table that the last SELECT statement selects from in the input query.
        """
        # Split the query into lines
        lines = sql.strip().split("\n")

        # Remove the starting WITH keyword
        if lines[0].strip().lower().startswith("with"):
            lines[0] = lines[0][4:].strip()

        # Identify the name of the table in the final SELECT statement
        table_name = None
        final_select_index = None
        for i, line in enumerate(lines):
            if line.strip().lower().startswith("select"):
                final_select_index = i
                # Extract the table name (assumes simple "SELECT * FROM table_name" structure)
                if "from" in line.lower():
                    table_name = line.lower().split("from")[-1].strip().split()[0]

        # Remove the lines related to the final SELECT
        if final_select_index is not None:
            lines = lines[:final_select_index]

        # Return the reshaped SQL code and the table name
        reshaped_sql = "\n".join(lines).strip()
        return reshaped_sql, table_name

    # Flatten assignments and entry point queries
    assignments_block, assignment_cte_name = process_query(assignments_query)
    entry_point_block, entry_point_cte_name = process_query(entry_point_query)

    # Extract column mappings for assignments and entry points
    assignments_id = assignments_mapping['randomisation_unit_id']
    assignments_variant = assignments_mapping['variant_column']
    assignments_date = assignments_mapping['date_column']

    entry_point_id = entry_point_mapping['randomisation_unit_id']
    entry_point_date = entry_point_mapping['date_column']

    # Generate the exposures CTE
    exposures_cte = (
        """
        exposures__customers as (
            select
                a.{assignments_id} as rand_unit_id,
                a.{assignments_variant} as variant,
                a.{assignments_date} as first_assignment_date,
                e.{entry_point_date} as entry_point_date
            from {assignments_sql} a
            inner join {entry_point_sql} e
            on a.{assignments_id} = e.{entry_point_id}
        )""".format(
            assignments_id=assignments_id,
            assignments_variant=assignments_variant,
            assignments_date=assignments_date,
            entry_point_date=entry_point_date,
            entry_point_id=entry_point_id,
            assignments_sql=assignment_cte_name,
            entry_point_sql=entry_point_cte_name
        )
    )

    # Generate the merge CTEs for each fact query
    merge_ctes = []
    fact_ctes = []
    for i, fact in enumerate(fact_queries):
        fact_block, fact_table_name = process_query(fact['query'])
        fact_mapping = fact['mapping']

        fact_id = fact_mapping['randomisation_unit_id']
        fact_date = fact_mapping['date_column']
        fact_columns = fact_mapping['fact_columns']

        # Create a COALESCE wrapper for each fact column
        coalesce_columns = [
            "coalesce(sum({col}), 0) as {col}".format(col=col)
            for col in fact_columns
        ]
        coalesce_columns_sql = ",\n            ".join(coalesce_columns)

        fact_ctes.append(fact_block)

        merge_cte = (
            """
            merge__fact_{i} as (
                select
                    e.rand_unit_id,
                    e.variant,
                    e.first_assignment_date,
                    e.entry_point_date,
                    {coalesce_columns_sql}
                from exposures__customers e
                left join {i} f
                on e.rand_unit_id = f.{fact_id} and (f.{fact_date} >= e.entry_point_date or f.{fact_date} is null)
                group by 1, 2, 3, 4
            )""".format(
                i=fact_table_name,
                coalesce_columns_sql=coalesce_columns_sql,
                fact_id=fact_id,
                fact_date=fact_date
            )
        )
        merge_ctes.append(merge_cte)

    # Final merge CTE combining all merge__fact CTEs
    final_merge_cte = "merge__all as (\n        select\n            rand_unit_id, variant, first_assignment_date, entry_point_date"
    for i, fact in enumerate(fact_queries):
        _, fact_table_name = process_query(fact['query'])
        fact_mapping = fact['mapping']
        fact_columns = fact_mapping['fact_columns']

        # Add each fact column to the final select statement
        for col in fact_columns:
            final_merge_cte += ",\n            merge__fact_{i}.{col}".format(i=fact_table_name, col=col)

    final_merge_cte += "\n        from exposures__customers"
    for i in range(len(fact_queries)):
        final_merge_cte += "\n        join merge__fact_{i} using(rand_unit_id, variant, first_assignment_date, entry_point_date)".format(i=fact_table_name)
    final_merge_cte += "\n    )"

    # Combine all CTEs into the final SQL
    final_sql = (
        """
        with 
        {assignments_block},
        {entry_point_block},
        {exposures_cte},
        {fact_ctes},
        {merge_ctes},
        {final_merge_cte}
        select * from merge__all
        """.format(
            assignments_block=assignments_block,
            entry_point_block=entry_point_block,
            fact_ctes=",\n    ".join(fact_ctes),
            exposures_cte=exposures_cte,
            merge_ctes=",\n    ".join(merge_ctes),
            final_merge_cte=final_merge_cte
        )
    )

    return final_sql.strip()