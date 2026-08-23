from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'assets'; OUT.mkdir(exist_ok=True)
df=pd.read_csv(ROOT/'data'/'cleaned_nassau_candy.csv',parse_dates=['Order Date'])
p=pd.read_csv(ROOT/'outputs'/'product_profitability.csv')
d=pd.read_csv(ROOT/'outputs'/'division_performance.csv')

plt.figure(figsize=(10,6))
t=p.sort_values('Gross_Profit')
plt.barh(t['Product Name'],t['Gross_Profit'])
plt.xlabel('Gross Profit ($)'); plt.title('Gross Profit by Product'); plt.tight_layout(); plt.savefig(OUT/'product_gross_profit.png',dpi=180); plt.close()

plt.figure(figsize=(9,5))
x=np.arange(len(d)); w=.36
plt.bar(x-w/2,d.Sales,w,label='Sales'); plt.bar(x+w/2,d.Gross_Profit,w,label='Gross Profit')
plt.xticks(x,d.Division); plt.ylabel('$'); plt.title('Division Revenue vs Gross Profit'); plt.legend(); plt.tight_layout(); plt.savefig(OUT/'division_revenue_profit.png',dpi=180); plt.close()

plt.figure(figsize=(9,5))
plt.scatter(p.Sales,p.Gross_Margin,s=np.maximum(p.Gross_Profit/20,25))
for _,r in p.iterrows():
    if r.Gross_Margin<.55 or r.Sales>20000: plt.annotate(r['Product Name'].replace('Wonka Bar - ','WB - '),(r.Sales,r.Gross_Margin),fontsize=7,xytext=(4,3),textcoords='offset points')
plt.axhline(.5,linestyle='--'); plt.gca().yaxis.set_major_formatter(lambda x,pos:f'{x:.0%}')
plt.xlabel('Sales ($)'); plt.ylabel('Gross Margin'); plt.title('Sales vs Gross Margin'); plt.tight_layout(); plt.savefig(OUT/'sales_vs_margin.png',dpi=180); plt.close()

for metric,fn,title in [('Sales','pareto_revenue.png','Revenue Pareto'),('Gross_Profit','pareto_profit.png','Profit Pareto')]:
    t=p.sort_values(metric,ascending=False).copy(); t['cum']=t[metric].cumsum()/t[metric].sum()
    fig,ax=plt.subplots(figsize=(10,5)); ax.bar(range(len(t)),t[metric]); ax.set_ylabel(metric.replace('_',' ')); ax.set_xticks(range(len(t))); ax.set_xticklabels(t['Product Name'],rotation=70,ha='right',fontsize=7)
    ax2=ax.twinx(); ax2.plot(range(len(t)),t['cum'],marker='o'); ax2.axhline(.8,linestyle='--'); ax2.set_ylim(0,1.05); ax2.yaxis.set_major_formatter(lambda x,pos:f'{x:.0%}'); ax2.set_ylabel('Cumulative Share')
    ax.set_title(title); fig.tight_layout(); fig.savefig(OUT/fn,dpi=180); plt.close(fig)
