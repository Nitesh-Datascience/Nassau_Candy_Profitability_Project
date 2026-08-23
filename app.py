from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'/'cleaned_nassau_candy.csv'

st.set_page_config(page_title='Nassau Candy Profitability', page_icon='🍬', layout='wide')

@st.cache_data
def load_data():
    df=pd.read_csv(DATA, parse_dates=['Order Date','Ship Date'])
    return df

def product_summary(df):
    p=df.groupby(['Product ID','Product Name','Division','Factory'],as_index=False).agg(
        Sales=('Sales','sum'),Cost=('Cost','sum'),Gross_Profit=('Gross Profit','sum'),Units=('Units','sum'),Orders=('Order ID','nunique'))
    p['Gross_Margin']=p['Gross_Profit']/p['Sales']
    p['Profit_per_Unit']=p['Gross_Profit']/p['Units']
    p['Revenue_Contribution']=p['Sales']/p['Sales'].sum()
    p['Profit_Contribution']=p['Gross_Profit']/p['Gross_Profit'].sum()
    p['Risk']=np.select([p.Gross_Margin<.20,p.Gross_Margin<.50,p.Gross_Margin<.60],['Critical','High','Watch'],default='Healthy')
    return p

def fmt_money(x): return f'${x:,.0f}'

raw=load_data()
st.title('Product Line Profitability & Margin Performance Analysis')
st.caption('Nassau Candy Distributor | Interactive profitability, margin risk, cost diagnostics and Pareto concentration')

with st.sidebar:
    st.header('Filters')
    min_date,max_date=raw['Order Date'].min().date(),raw['Order Date'].max().date()
    dr=st.date_input('Order date range',(min_date,max_date),min_value=min_date,max_value=max_date)
    divisions=st.multiselect('Division',sorted(raw.Division.unique()),default=sorted(raw.Division.unique()))
    margin_threshold=st.slider('Margin risk threshold',0,100,50,1,help='Products below this gross-margin % are highlighted as risk.')/100
    search=st.text_input('Product search','').strip().lower()
    st.divider()
    st.caption('Data-quality note: shipment dates are not used for delivery-time conclusions because their range is inconsistent with order dates.')

start,end=(dr if isinstance(dr,(tuple,list)) and len(dr)==2 else (min_date,max_date))
df=raw[(raw['Order Date'].dt.date>=start)&(raw['Order Date'].dt.date<=end)&raw.Division.isin(divisions)].copy()
if search:
    df=df[df['Product Name'].str.lower().str.contains(search,na=False)]

if df.empty:
    st.warning('No records match the selected filters.')
    st.stop()

p=product_summary(df)
total_sales=df.Sales.sum(); total_profit=df['Gross Profit'].sum(); total_cost=df.Cost.sum(); units=df.Units.sum(); gm=total_profit/total_sales

c1,c2,c3,c4,c5=st.columns(5)
c1.metric('Sales',fmt_money(total_sales)); c2.metric('Gross Profit',fmt_money(total_profit)); c3.metric('Gross Margin',f'{gm:.1%}'); c4.metric('Units',f'{units:,.0f}'); c5.metric('Profit / Unit',f'${total_profit/units:,.2f}')

tabs=st.tabs(['Overview','Division Performance','Cost & Margin Diagnostics','Pareto Concentration','Data Explorer'])

with tabs[0]:
    left,right=st.columns([1.2,1])
    with left:
        top=p.sort_values('Gross_Profit',ascending=True)
        fig=px.bar(top,y='Product Name',x='Gross_Profit',orientation='h',title='Gross Profit by Product',hover_data=['Sales','Gross_Margin','Profit_per_Unit'])
        fig.update_layout(xaxis_title='Gross Profit ($)',yaxis_title='')
        st.plotly_chart(fig,use_container_width=True)
    with right:
        margin=p.sort_values('Gross_Margin',ascending=False)
        fig=px.bar(margin,x='Gross_Margin',y='Product Name',orientation='h',title='Product Gross Margin Leaderboard')
        fig.add_vline(x=margin_threshold,line_dash='dash',annotation_text=f'Threshold {margin_threshold:.0%}')
        fig.update_layout(xaxis_tickformat='.0%',xaxis_title='Gross Margin',yaxis_title='')
        st.plotly_chart(fig,use_container_width=True)
    risk=p[p.Gross_Margin<margin_threshold].sort_values('Gross_Margin')
    st.subheader('Margin Risk Flags')
    if risk.empty: st.success('No products fall below the selected margin threshold.')
    else: st.dataframe(risk[['Product Name','Division','Factory','Sales','Gross_Profit','Gross_Margin','Profit_per_Unit']].style.format({'Sales':'${:,.2f}','Gross_Profit':'${:,.2f}','Gross_Margin':'{:.1%}','Profit_per_Unit':'${:,.2f}'}),use_container_width=True,hide_index=True)

with tabs[1]:
    d=df.groupby('Division',as_index=False).agg(Sales=('Sales','sum'),Gross_Profit=('Gross Profit','sum'),Cost=('Cost','sum'),Units=('Units','sum'))
    d['Gross_Margin']=d.Gross_Profit/d.Sales
    d['Revenue_Share']=d.Sales/d.Sales.sum(); d['Profit_Share']=d.Gross_Profit/d.Gross_Profit.sum()
    a,b=st.columns(2)
    with a:
        melted=d.melt(id_vars='Division',value_vars=['Sales','Gross_Profit'],var_name='Metric',value_name='Value')
        st.plotly_chart(px.bar(melted,x='Division',y='Value',color='Metric',barmode='group',title='Revenue vs Gross Profit by Division'),use_container_width=True)
    with b:
        fig=px.bar(d,x='Division',y='Gross_Margin',title='Gross Margin by Division',text=d.Gross_Margin.map(lambda x:f'{x:.1%}'))
        fig.update_layout(yaxis_tickformat='.0%')
        st.plotly_chart(fig,use_container_width=True)
    st.dataframe(d.style.format({'Sales':'${:,.2f}','Gross_Profit':'${:,.2f}','Cost':'${:,.2f}','Gross_Margin':'{:.1%}','Revenue_Share':'{:.1%}','Profit_Share':'{:.1%}'}),use_container_width=True,hide_index=True)

with tabs[2]:
    a,b=st.columns(2)
    with a:
        fig=px.scatter(p,x='Sales',y='Cost',size='Gross_Profit',color='Gross_Margin',hover_name='Product Name',title='Product Cost vs Sales',labels={'Gross_Margin':'Gross Margin'})
        fig.add_trace(go.Scatter(x=[0,max(p.Sales)*1.05],y=[0,max(p.Sales)*1.05],mode='lines',name='Cost = Sales',line=dict(dash='dash')))
        st.plotly_chart(fig,use_container_width=True)
    with b:
        fig=px.scatter(p,x='Sales',y='Gross_Margin',size='Gross_Profit',color='Division',hover_name='Product Name',title='Sales vs Margin: Volume Can Hide Margin Risk')
        fig.add_hline(y=margin_threshold,line_dash='dash',annotation_text='Risk threshold')
        fig.update_layout(yaxis_tickformat='.0%')
        st.plotly_chart(fig,use_container_width=True)
    diag=p.assign(Cost_Ratio=p.Cost/p.Sales).sort_values(['Gross_Margin','Sales'])
    st.subheader('Action-Oriented Diagnostics')
    diag['Suggested_Action']=np.select([diag.Gross_Margin<.20,diag.Gross_Margin<.50,diag.Gross_Margin<.60],['Discontinuation / urgent reprice review','Reprice or renegotiate cost','Monitor and test pricing'],default='Maintain / scale selectively')
    st.dataframe(diag[['Product Name','Factory','Sales','Cost','Gross_Profit','Gross_Margin','Cost_Ratio','Suggested_Action']].style.format({'Sales':'${:,.2f}','Cost':'${:,.2f}','Gross_Profit':'${:,.2f}','Gross_Margin':'{:.1%}','Cost_Ratio':'{:.1%}'}),use_container_width=True,hide_index=True)

with tabs[3]:
    metric=st.radio('Pareto metric',['Gross Profit','Sales'],horizontal=True)
    col='Gross_Profit' if metric=='Gross Profit' else 'Sales'
    par=p.sort_values(col,ascending=False).copy(); par['CumShare']=par[col].cumsum()/par[col].sum(); par['Rank']=range(1,len(par)+1)
    threshold_count=int((par.CumShare<.8).sum()+1)
    fig=go.Figure()
    fig.add_bar(x=par['Product Name'],y=par[col],name=metric)
    fig.add_scatter(x=par['Product Name'],y=par.CumShare,name='Cumulative Share',yaxis='y2',mode='lines+markers')
    fig.update_layout(title=f'{metric} Pareto Analysis',yaxis2=dict(overlaying='y',side='right',tickformat='.0%',range=[0,1.05]),xaxis_tickangle=-45)
    st.plotly_chart(fig,use_container_width=True)
    st.info(f'{threshold_count} of {len(par)} products ({threshold_count/len(par):.1%}) generate at least 80% of {metric.lower()} under the current filters.')
    st.dataframe(par[['Rank','Product Name',col,'CumShare']].style.format({col:'${:,.2f}','CumShare':'{:.1%}'}),use_container_width=True,hide_index=True)

with tabs[4]:
    st.subheader('Filtered Transaction Data')
    st.download_button('Download filtered CSV',df.to_csv(index=False).encode('utf-8'),'nassau_filtered.csv','text/csv')
    st.dataframe(df,use_container_width=True,hide_index=True)
