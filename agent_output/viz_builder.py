import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def build_chart(df: pd.DataFrame, chart_config: dict) -> go.Figure:
    """
    Builds a Plotly chart based on the provided DataFrame and chart configuration.
    """
    chart_type = chart_config.get('type')
    title = chart_config.get('title', 'Untitled Chart')
    
    if chart_type == "Bar Chart":
        x_col = chart_config.get('x_col')
        y_col = chart_config.get('y_col')
        color_col = chart_config.get('color_col')
        if x_col and y_col:
            fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = go.Figure().add_annotation(text="Missing X/Y columns for Bar Chart", xref="paper", yref="paper", showarrow=False, font=dict(size=18))
    elif chart_type == "Line Chart":
        x_col = chart_config.get('x_col')
        y_col = chart_config.get('y_col')
        color_col = chart_config.get('color_col')
        if x_col and y_col:
            fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = go.Figure().add_annotation(text="Missing X/Y columns for Line Chart", xref="paper", yref="paper", showarrow=False, font=dict(size=18))
    elif chart_type == "Pie Chart":
        names_col = chart_config.get('names_col')
        values_col = chart_config.get('values_col')
        if names_col and values_col:
            fig = px.pie(df, names=names_col, values=values_col, title=title)
        else:
            fig = go.Figure().add_annotation(text="Missing Names/Values columns for Pie Chart", xref="paper", yref="paper", showarrow=False, font=dict(size=18))
    elif chart_type == "Scatter Plot":
        x_col = chart_config.get('x_col')
        y_col = chart_config.get('y_col')
        color_col = chart_config.get('color_col')
        size_col = chart_config.get('size_col')
        if x_col and y_col:
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, size=size_col, title=title)
        else:
            fig = go.Figure().add_annotation(text="Missing X/Y columns for Scatter Plot", xref="paper", yref="paper", showarrow=False, font=dict(size=18))
    elif chart_type == "Area Chart":
        x_col = chart_config.get('x_col')
        y_col = chart_config.get('y_col')
        color_col = chart_config.get('color_col')
        if x_col and y_col:
            fig = px.area(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = go.Figure().add_annotation(text="Missing X/Y columns for Area Chart", xref="paper", yref="paper", showarrow=False, font=dict(size=18))
    elif chart_type == "Histogram":
        x_col = chart_config.get('x_col')
        color_col = chart_config.get('color_col')
        if x_col:
            fig = px.histogram(df, x=x_col, color=color_col, title=title)
        else:
            fig = go.Figure().add_annotation(text="Missing X column for Histogram", xref="paper", yref="paper", showarrow=False, font=dict(size=18))
    elif chart_type == "KPI Metric":
        value_col = chart_config.get('value_col')
        delta_col = chart_config.get('delta_col')
        
        if value_col and not df.empty:
            value = df[value_col].iloc[0] if not df[value_col].isnull().all() else None
            
            delta = None
            if delta_col and not df[delta_col].isnull().all():
                delta = df[delta_col].iloc[0] # Assuming delta is pre-calculated difference
            
            fig = go.Figure(go.Indicator(
                mode="number+delta",
                value=value,
                delta={"reference": value - delta if delta is not None else None, "relative": False},
                title={"text": title}
            ))
            fig.update_layout(height=200) # Smaller height for KPI
        else:
            fig = go.Figure().add_annotation(text="Missing Value column or no data for KPI", xref="paper", yref="paper", showarrow=False, font=dict(size=18))
    else:
        fig = go.Figure().add_annotation(text=f"Unsupported chart type: {chart_type}", xref="paper", yref="paper", showarrow=False, font=dict(size=18))

    if 'fig' in locals() and fig:
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified"
        )
    return fig