import sqlite3
import os
from pathlib import Path
import pandas as pd

from barbucket.database import DataBase
from barbucket.contracts_db import ContractsDB


class ContractDetailsDB(DataBase):

    def __init__(self):
        self.__contracts_db = ContractsDB()


    def insert_ib_contract_details(self, contract_id, industry, category,
        subcategrory, ib_con_id, primary_exchange, stock_type):

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""REPLACE INTO contract_details_ib (contract_id, industry,
            category, subcategrory, ib_con_id, primary_exchange, stock_typus) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""", (contract_id, industry, category,
            subcategrory, ib_con_id, primary_exchange, stock_type))

        conn.commit()
        cur.close()
        self.disconnect(conn)


    def get_ib_contract_details(self, contract_id):

        query = f"""SELECT contract_id, industry, category, subcategrory,
                        ib_con_id, primary_exchange, stock_typus
                    FROM contract_details_ib
                    WHERE contract_id = {contract_id};"""

        conn = self.connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(query)
        result = cur.fetchall()

        conn.commit()
        cur.close()
        self.disconnect(conn)

        if len(result) > 0:
            return result[0]
        else:
            return None


    def __insert_tw_details(self, contract_id, market_cap, avg_vol_30_in_curr,
            country, employees, profit, revenue):

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""REPLACE INTO contract_details_tw (contract_id, market_cap,
            avg_vol_30_in_curr, country, employees, profit, revenue) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""", (contract_id, market_cap,
            avg_vol_30_in_curr, country, employees, profit, revenue))

        conn.commit()
        cur.close()
        self.disconnect(conn)


    def ingest_tw_files(self):

        # Exchange codes
        exchange_codes = {
            "NASDAQ": "ISLAND",
            "NYSE": "NYSE",
            "NYSE ARCA": "ARCA",
            "AMEX": "AMEX",
            "FWB": "FWB",
            "IBIS": "IBIS",
            "LSE": "LSE",
            "LSEETF": "LSEETF"}
        
        mypath = Path.home() / ".barbucket/tw_screener"
        screener_files = [f for f in os.listdir(mypath) if
            os.path.isfile(os.path.join(mypath, f))]

        for file in screener_files:
            if file.startswith("Done_"):
                continue

            df = pd.read_csv(mypath / file, sep=",")

            for _, row in df.iterrows():

                # Get contract id
                ticker =row["Ticker"].replace(".", " ")
                result = self.__contracts_db.get_contracts(
                    exchange_symbol=ticker,
                    exchange=exchange_codes[row["Exchange"]])

                if len(result) == 1:
                    # Write details to db
                    contract_id = result[0]["contract_id"]
                    avg_vol_30_in_curr = row["Average Volume (30 day)"] * \
                        row["Simple Moving Average (30)"]
                    if pd.isna(avg_vol_30_in_curr):
                        avg_vol_30_in_curr = 0
                    else:
                        avg_vol_30_in_curr = int(avg_vol_30_in_curr)
                    if pd.isna(row["Number of Employees"]):
                        employees = 0
                    else:
                        employees = int(row["Number of Employees"])
                    if pd.isna(row["Gross Profit (FY)"]):
                        profit = 0
                    else:
                        profit = int(row["Gross Profit (FY)"])
                    if pd.isna(row["Total Revenue (FY)"]):
                        revenue = 0
                    else:
                        revenue = int(row["Total Revenue (FY)"])
                        
                    self.__insert_tw_details(
                        contract_id=contract_id,
                        market_cap=row["Market Capitalization"],
                        avg_vol_30_in_curr=avg_vol_30_in_curr,
                        country=row["Country"],
                        employees=employees,
                        profit=profit,
                        revenue=revenue)
                else:
                    ticker =row["Ticker"]
                    exchange = row["Exchange"]
                    print(f"Error: {len(result)} results for {ticker} \
                        on {exchange}.")

            # Rename file
            os.rename(mypath / file, mypath / ("Done_" + file))


