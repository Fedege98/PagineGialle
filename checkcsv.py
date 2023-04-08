import pandas as pd

df = pd.read_csv('prova.csv')
print(df['ID'].dtype)
