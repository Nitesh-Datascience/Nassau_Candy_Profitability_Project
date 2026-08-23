from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw_nassau_candy.csv'
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)

FACTORY_MAP = {
    'Wonka Bar - Nutty Crunch Surprise': ("Lot's O' Nuts", 32.881893, -111.768036),
    'Wonka Bar - Fudge Mallows': ("Lot's O' Nuts", 32.881893, -111.768036),
    'Wonka Bar -Scrumdiddlyumptious': ("Lot's O' Nuts", 32.881893, -111.768036),
    'Wonka Bar - Milk Chocolate': ("Wicked Choccy's", 32.076176, -81.088371),
    'Wonka Bar - Triple Dazzle Caramel': ("Wicked Choccy's", 32.076176, -81.088371),
    'Laffy Taffy': ('Sugar Shack', 48.11914, -96.18115),
    'SweeTARTS': ('Sugar Shack', 48.11914, -96.18115),
    'Nerds': ('Sugar Shack', 48.11914, -96.18115),
    'Fun Dip': ('Sugar Shack', 48.11914, -96.18115),
    'Fizzy Lifting Drinks': ('Sugar Shack', 48.11914, -96.18115),
    'Everlasting Gobstopper': ('Secret Factory', 41.446333, -90.565487),
    'Hair Toffee': ('The Other Factory', 35.1175, -89.971107),
    'Lickable Wallpaper': ('Secret Factory', 41.446333, -90.565487),
    'Wonka Gum': ('Secret Factory', 41.446333, -90.565487),
    'Kazookles': ('The Other Factory', 35.1175, -89.971107),
}

def load_clean():
    df = pd.read_csv(RAW)
    for c in ['Order Date', 'Ship Date']:
        df[c] = pd.to_datetime(df[c], dayfirst=True, errors='coerce')
    for c in ['Division','Product Name','Product ID','Region','State/Province']:
        df[c] = df[c].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
    # Normalize known product spelling while preserving semantic name.
    df['Product Name'] = df['Product Name'].replace({'Wonka Bar -Scrumdiddlyumptious':'Wonka Bar - Scrumdiddlyumptious'})
    factory_map_norm = {k.replace('Wonka Bar -Scrumdiddlyumptious','Wonka Bar - Scrumdiddlyumptious'): v for k,v in FACTORY_MAP.items()}
    f = df['Product Name'].map(factory_map_norm)
    df['Factory'] = f.map(lambda x: x[0] if isinstance(x, tuple) else 'Unmapped')
    df['Factory Latitude'] = f.map(lambda x: x[1] if isinstance(x, tuple) else np.nan)
    df['Factory Longitude'] = f.map(lambda x: x[2] if isinstance(x, tuple) else np.nan)
    df['Calculated Profit'] = df['Sales'] - df['Cost']
    df['Profit Reconciliation Error'] = df['Gross Profit'] - df['Calculated Profit']
    df['Gross Margin'] = np.where(df['Sales'] > 0, df['Gross Profit']/df['Sales'], np.nan)
    df['Profit per Unit'] = np.where(df['Units'] > 0, df['Gross Profit']/df['Units'], np.nan)
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
    valid = (df['Sales'] > 0) & (df['Units'] > 0) & df[['Sales','Cost','Gross Profit']].notna().all(axis=1)
    return df.loc[valid].copy()

def product_summary(df):
    p = df.groupby(['Product ID','Product Name','Division','Factory'], as_index=False).agg(
        Sales=('Sales','sum'), Cost=('Cost','sum'), Gross_Profit=('Gross Profit','sum'),
        Units=('Units','sum'), Orders=('Order ID','nunique'))
    p['Gross_Margin'] = p['Gross_Profit']/p['Sales']
    p['Profit_per_Unit'] = p['Gross_Profit']/p['Units']
    p['Revenue_Contribution'] = p['Sales']/p['Sales'].sum()
    p['Profit_Contribution'] = p['Gross_Profit']/p['Gross_Profit'].sum()
    monthly = df.groupby(['Product ID','Month'], as_index=False).agg(Sales=('Sales','sum'), Gross_Profit=('Gross Profit','sum'))
    monthly['Margin'] = monthly['Gross_Profit']/monthly['Sales']
    vol = monthly.groupby('Product ID',as_index=False)['Margin'].std().rename(columns={'Margin':'Margin_Volatility'}).fillna(0)
    p = p.merge(vol,on='Product ID',how='left')
    p['Margin_Risk_Flag'] = np.select(
        [p['Gross_Margin'] < .20, p['Gross_Margin'] < .50, (p['Gross_Margin'] < .60) & (p['Sales'] > p['Sales'].median())],
        ['Critical','High','Watch'], default='Healthy')
    return p.sort_values('Gross_Profit',ascending=False)

def division_summary(df):
    d = df.groupby('Division',as_index=False).agg(Sales=('Sales','sum'), Cost=('Cost','sum'), Gross_Profit=('Gross Profit','sum'), Units=('Units','sum'), Products=('Product ID','nunique'), Orders=('Order ID','nunique'))
    d['Gross_Margin'] = d['Gross_Profit']/d['Sales']
    d['Profit_per_Unit'] = d['Gross_Profit']/d['Units']
    d['Revenue_Share'] = d['Sales']/d['Sales'].sum()
    d['Profit_Share'] = d['Gross_Profit']/d['Gross_Profit'].sum()
    d['Profit_to_Revenue_Index'] = d['Profit_Share']/d['Revenue_Share']
    return d.sort_values('Gross_Profit',ascending=False)

def pareto(summary, metric):
    t = summary.sort_values(metric,ascending=False).copy()
    t[f'{metric}_Share'] = t[metric]/t[metric].sum()
    t[f'{metric}_Cumulative_Share'] = t[f'{metric}_Share'].cumsum()
    t['Rank'] = range(1,len(t)+1)
    return t

if __name__ == '__main__':
    df=load_clean(); p=product_summary(df); d=division_summary(df)
    df.to_csv(ROOT/'data'/'cleaned_nassau_candy.csv',index=False)
    p.to_csv(OUT/'product_profitability.csv',index=False)
    d.to_csv(OUT/'division_performance.csv',index=False)
    pareto(p,'Sales').to_csv(OUT/'pareto_revenue.csv',index=False)
    pareto(p,'Gross_Profit').to_csv(OUT/'pareto_profit.csv',index=False)
    print(f'Clean rows: {len(df):,}')
    print(f'Total Sales: ${df.Sales.sum():,.2f}')
    print(f'Total Gross Profit: ${df["Gross Profit"].sum():,.2f}')
    print(f'Overall Gross Margin: {df["Gross Profit"].sum()/df.Sales.sum():.2%}')
