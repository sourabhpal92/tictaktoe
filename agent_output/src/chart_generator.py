import altair as alt
import pandas as pd

def generate_chart(df: pd.DataFrame, chart_config: dict):
    """
    Generates an Altair chart based on the provided DataFrame and configuration.
    """
    chart_type = chart_config.get("chart_type")
    x_col = chart_config.get("x_col")
    y_col = chart_config.get("y_col")
    color_col = chart_config.get("color_col")
    title = chart_config.get("title", f"{chart_type.capitalize()} Chart")
    aggregation = chart_config.get("aggregation", "mean") # Default aggregation for Y-axis

    if not df.empty and x_col in df.columns and y_col in df.columns:
        base = alt.Chart(df).encode(
            x=alt.X(x_col, type=str(df[x_col].dtype)), # Infer type
            y=alt.Y(f'{aggregation}({y_col})' if df[y_col].dtype != 'object' else y_col, # Apply aggregation if numeric
                    type=str(df[y_col].dtype))
        ).properties(
            title=title
        )

        if color_col and color_col in df.columns:
            base = base.encode(color=alt.Color(color_col, type=str(df[color_col].dtype)))

        if chart_type == "bar":
            chart = base.mark_bar()
        elif chart_type == "line":
            chart = base.mark_line(point=True)
        elif chart_type == "area":
            chart = base.mark_area(opacity=0.7)
        elif chart_type == "scatter":
            chart = base.mark_circle(size=60)
        elif chart_type == "pie":
            # For pie charts, y_col usually represents the value for slices
            if y_col and df[y_col].dtype != 'object': # Ensure y_col is numeric for aggregation
                chart = alt.Chart(df).encode(
                    theta=alt.Theta(field=y_col, type="quantitative", stack=True),
                    color=alt.Color(x_col, type="nominal", title=x_col)
                ).mark_arc(outerRadius=120).properties(
                    title=title
                )
                text = chart.mark_text(radius=140).encode(
                    text=alt.Text(field=y_col, type="quantitative"),
                    order=alt.Order(field=y_col, sort="descending"),
                    color=alt.value("black")
                )
                return chart + text
            else:
                return None # Pie chart requires a quantitative field

        else:
            return None # Unsupported chart type

        # Add tooltips for interactivity
        tooltip_cols = [x_col, y_col]
        if color_col:
            tooltip_cols.append(color_col)
        chart = chart.encode(
            tooltip=tooltip_cols
        ).interactive() # Make chart interactive (zoom, pan)

        return chart
    return None

def generate_kpi_metric(df: pd.DataFrame, column: str, aggregation: str):
    """
    Generates a single KPI metric.
    """
    if not df.empty and column in df.columns:
        value = None
        if df[column].dtype != 'object': # Only aggregate numeric columns
            if aggregation == "sum":
                value = df[column].sum()
            elif aggregation == "mean":
                value = df[column].mean()
            elif aggregation == "count":
                value = df[column].count()
            elif aggregation == "min":
                value = df[column].min()
            elif aggregation == "max":
                value = df[column].max()
            else:
                value = df[column].iloc[0] # Default to first value if no aggregation

            return f"{value:,.2f}" # Format as currency/number with commas and 2 decimal places
        else:
            # For non-numeric, count unique values or just show first if count not requested
            if aggregation == "count":
                value = df[column].nunique()
                return f"{value}"
            elif not df.empty:
                return str(df[column].iloc[0])

    return "N/A"