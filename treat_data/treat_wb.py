#%%
"""
This script reads the data from the World Bank excel file and treats it to be used in the project.
The data is about carbon taxes and ETS and includes information about the instrument, the price, the revenue and the emissions.

Layout notes (World Bank file, edition May 2026):
- Header rows are located by their first cell, not by a fixed row number, because the sheets
  carry a variable number of note rows above the table.
- "Status" no longer carries the start year and "Type" no longer carries the scope (national/subnational).
  Start Year and Subtype are taken from the previous processed table (data/processed/wb_info.csv)
  when the instrument already existed there; for new instruments they are derived (see below)
  and printed at the end of the run so they can be reviewed.
- "Share of jurisdiction emissions covered" is a text such as
  "73% of jurisdiction emissions, 0.0098% of global emissions" and is split in two numeric columns.
- "Start Year derived" marks the start years that the World Bank does not give and that were derived
  from the data or set by hand (START_YEAR_MANUAL); the mark is carried over from the previous table.

The crediting sheets (Crediting_Detail, Crediting_Issuance, Cooperative Approaches) are treated by
update_wb_crediting() and saved in wb_crediting_info.csv, wb_crediting_issuance.csv and wb_cooperative.csv.
"""

import pandas as pd
import numpy as np
import re
import os

meses = {
    "January": "Janeiro",
    "February": "Fevereiro",
    "March": "Março",
    "April": "Abril",
    "May": "Maio",
    "June": "Junho",
    "July": "Julho",
    "August": "Agosto",
    "September": "Setembro",
    "October": "Outubro",
    "November": "Novembro",
    "December": "Dezembro"
}

# Subnational instruments that are cities (the file only gives the jurisdiction name)
CIDADES = {"Minneapolis", "Mexico City"}
# Jurisdictions whose ID carries a suffix but that are national
NACIONAIS_COM_SUFIXO = {"Taiwan, China"}

# Start years set by hand (decision of 01/10/2026), always marked as derived. Keys are normalised names.
# Taiwan: the World Bank description says the carbon fee was "Launched on January 1, 2025" (the price series starts in 2024).
# Minneapolis: no description in the file; the only year with price is 2026.
START_YEAR_MANUAL = {"taiwan, china carbon fee": 2025, "minneapolis carbon tax": 2026}
# Scope set by hand (decision of 01/10/2026): Taiwan ETS is national, like the Taiwan carbon fee
SUBTYPE_MANUAL = {"taiwan, china ets": "Nacional"}


def translate_date(text):
    """'April 1, 2026' -> 'Abril 1, 2026' (format used in data/update_info.csv)."""
    for en, pt in meses.items():
        text = text.replace(en, pt)
    return text.strip()


def _norm(name):
    """Normalise instrument names: the World Bank changes capitalisation and spaces between editions."""
    return re.sub(r"\s+", " ", str(name).replace("\xa0", " ")).strip().lower()


def _read_sheet(file_path, sheet_name, first_col):
    """Read a sheet whose header row starts with `first_col`."""
    raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    header_row = raw.index[raw.iloc[:, 0].astype(str).str.strip() == first_col][0]
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
    df.columns = [int(c) if isinstance(c, float) and c == int(c) else c for c in df.columns]
    return df


def _first_positive_year(df):
    """First year (column) in which each row has a value above zero."""
    def first(row):
        v = pd.to_numeric(row, errors="coerce")
        v = v[v > 0]
        return int(v.index[0]) if len(v) else np.nan
    year_cols = [c for c in df.columns if isinstance(c, int)]
    return df[year_cols].apply(first, axis=1)


def _parse_share(text, kind):
    """Extract a share (as fraction) from "73% of jurisdiction emissions, 0.0098% of global emissions"."""
    if isinstance(text, (int, float)):
        return text if kind == "jurisdiction" else np.nan
    match = re.search(rf"([\d.,]+)\s*%\s*of\s*{kind}\s*emissions", str(text))
    return float(match.group(1).replace(",", "")) / 100 if match else np.nan


def update_wb(file_path='data/raw/dados_wb.xlsx',
              save_path="data/processed",
              countries_info_data="data/extra_country_info.csv"):
    """
    This function reads the data from the World Bank excel file and treats it to be used in the project.

    Args:
        file_path (str): The path to the excel file.
        save_path (str): The path to save the processed data.
        countries_info_data (str): Optional path to a csv file with additional country information. (Expected columns: Jurisdiction;Income Group;Region)
    """
    #get update info
    last_update = translate_date(pd.read_excel(file_path, nrows=1, usecols=[0]).columns[0]\
                        .replace("Data last updated ",""))

    last_update_db = pd.read_csv('data/update_info.csv',index_col=0)
    last_update_db.loc['WB'] = last_update

    #previous table (used to keep start year and scope of instruments that already existed)
    old_path = f"{save_path}/wb_info.csv"
    if os.path.exists(old_path):
        old = pd.read_csv(old_path, sep=";", decimal=",")
        old["key"] = old["Instrument name"].map(_norm)
        old = old.drop_duplicates("key").set_index("key")
    else:
        old = pd.DataFrame(columns=["Start Year", "End Year", "Subtype", "Region", "Income group", "Jurisdiction covered"])
    if "Start Year derived" not in old.columns:
        old["Start Year derived"] = False

    #read data
    df_info = _read_sheet(file_path, 'Compliance_Gen Info', 'Unique ID')

    df_info = df_info.replace(" ", np.nan)\
            .dropna(axis=0,how='all')\
            .dropna(axis=1, how='all')

    #names
    df_info["Instrument name"] = df_info["Instrument name"].str.replace("\xa0", " ").str.strip()
    df_info["Jurisdiction covered"] = df_info["Jurisdiction covered"].str.strip()
    df_info["key"] = df_info["Instrument name"].map(_norm)

    # Sectors Covered
    # Replace "Yes", "No", and "In principle" with 1, 0, and 0 respectively
    # Create a new column that lists the columns where the value is 1 in that row
    df_info['Sectors Covered'] = df_info[['Electricity and heat',
                        'Industry',
                        'Mining and extractives',
                        'Transport',
                        'Aviation',
                        'Buildings',
                        'Agriculture, forestry and fishing fuel use',
                        'Agricultural emissions',
                        'Waste',
                        'LULUCF']].replace({"Yes": 1, 'No': 0, "In principle": 0})\
                            .apply(lambda row: ', '.join(row.index[row == 1].tolist()), axis=1)

    #shares of emissions covered (text -> two numeric columns)
    shares = df_info["Share of jurisdiction emissions covered"]
    df_info["Share of global emissions covered"] = shares.map(lambda x: _parse_share(x, "global"))
    df_info["Share of jurisdiction emissions covered"] = shares.map(lambda x: _parse_share(x, "jurisdiction"))
    unparsed = df_info[shares.notnull() & df_info["Share of global emissions covered"].isnull()]["Instrument name"].values
    print("Share of emissions covered not parsed:", unparsed, '\n')

    #status
    def extract_status(x):
            if "Abolished" in x:
                return "Abolished"
            match = re.search(r'(Implemented|Under consideration|Under development)', x)
            return match.group(1) if match else None

    df_info["Status"] = df_info["Status"].apply(extract_status)

    #price sheet (also gives region and income group)
    df_price = _read_sheet(file_path, 'Compliance_Price', 'Unique ID').replace("-",np.nan)
    df_price["key"] = df_price["Name of the initiative"].str.replace("\xa0", " ").map(_norm)

    #series (price, revenue, emissions) -- built before the start year, which is derived from them
    df_revenue = _read_sheet(file_path, 'Compliance_Revenue', 'Instrument name')\
                    .replace("Not available",np.nan)
    df_emissions = _read_sheet(file_path, 'Compliance_Emissions', 'Name of the initiative')\
                    .dropna(how='all')
    df_emissions["key"] = df_emissions["Name of the initiative"].map(_norm)

    #start year: previous table first, then first year with coverage, then first year with price
    start_emissions = df_emissions.set_index("key").pipe(_first_positive_year)
    start_price = df_price.set_index("key").pipe(_first_positive_year)
    derived_start = df_info["key"].map(start_emissions).fillna(df_info["key"].map(start_price))
    # for instruments not implemented the year is the one the previous table had (year they entered
    # consideration/development); the file no longer gives it, so new ones stay without year
    df_info["Start Year"] = df_info["key"].map(old["Start Year"])
    started = df_info["Status"].isin(["Implemented", "Abolished"])
    df_info["Start Year derived"] = df_info["key"].map(old["Start Year derived"]).fillna(False).astype(bool)
    to_derive = started & df_info["Start Year"].isnull()
    df_info.loc[to_derive, "Start Year"] = derived_start[to_derive]
    df_info.loc[to_derive & df_info["Start Year"].notnull(), "Start Year derived"] = True
    manual = df_info["key"].isin(START_YEAR_MANUAL)
    df_info.loc[manual, "Start Year"] = df_info.loc[manual, "key"].map(START_YEAR_MANUAL)
    df_info.loc[manual, "Start Year derived"] = True
    df_info["End Year"] = df_info["key"].map(old["End Year"])

    new_start = df_info[df_info["Start Year"].notnull() & ~df_info["key"].isin(old.index)]
    print("Start Year derived from the data (new instruments):")
    print(new_start[["Instrument name", "Start Year"]].to_string(index=False), '\n')
    print("Implemented/Abolished without Start Year:",
          df_info[df_info["Status"].isin(["Implemented", "Abolished"]) & df_info["Start Year"].isnull()]["Instrument name"].values, '\n')

    #share of global emissions covered: the text column in Gen Info is the gross share (it ignores the overlap
    #between instruments); the Emissions sheet accounts for overlaps, so its last year is used for implemented instruments
    last_em_year = max(c for c in df_emissions.columns if isinstance(c, int))
    share_net = df_emissions.set_index("key")[last_em_year]
    net = df_info["key"].map(share_net)
    implemented = df_info["Status"] == "Implemented"
    no_net = df_info[implemented & net.isnull()]["Instrument name"].values
    print(f"Implemented without {last_em_year} share in the Emissions sheet (gross share from Gen Info kept):", no_net, '\n')
    df_info["Share of global emissions covered"] = np.where(implemented, net.fillna(df_info["Share of global emissions covered"]), np.nan)
    # one instrument can be listed under several jurisdictions (EU ETS: EU27+, Iceland, Liechtenstein, Norway) with the
    # same share; keep it only in the first row, otherwise the pages that sum the column count it several times
    repeated = df_info["Instrument name"].duplicated()
    print("Rows of repeated instruments (global share kept only in the first):",
          df_info[repeated][["Instrument name", "Jurisdiction covered"]].values.tolist(), '\n')
    df_info.loc[repeated, "Share of global emissions covered"] = np.nan

    #region and income group
    regions_map = df_price.set_index("key")["Region"].to_dict()
    income_g = df_price.set_index("key")["Income group"].to_dict()
    revenue_income = df_revenue.set_index(df_revenue["Instrument name"].map(_norm))["Country income group"].to_dict()

    df_info["Region"] = df_info["key"].map(regions_map).fillna(df_info["key"].map(old["Region"]))
    df_info["Income group"] = df_info["key"].map(income_g)\
                                .fillna(df_info["key"].map(revenue_income))\
                                .fillna(df_info["key"].map(old["Income group"]))

    #same jurisdiction, other instruments (e.g. "Albania ETS" takes the data of "Albania carbon tax"), then the previous table
    for col in ["Region", "Income group"]:
        by_jurisdiction = df_info.dropna(subset=[col]).drop_duplicates("Jurisdiction covered").set_index("Jurisdiction covered")[col]
        old_by_jurisdiction = old.dropna(subset=[col]).drop_duplicates("Jurisdiction covered").set_index("Jurisdiction covered")[col] \
                                if "Jurisdiction covered" in old.columns else pd.Series(dtype=object)
        df_info[col] = df_info[col].fillna(df_info["Jurisdiction covered"].map(by_jurisdiction))\
                                   .fillna(df_info["Jurisdiction covered"].map(old_by_jurisdiction))

    #additional info (optional): overrides region and income group by jurisdiction
    if os.path.exists(countries_info_data):
        info = pd.read_csv(countries_info_data,sep=";", index_col=0)
        df_info["Region"] = df_info["Jurisdiction covered"].map(info['Region'].dropna().to_dict()).fillna(df_info["Region"])
        df_info["Income group"] = df_info["Jurisdiction covered"].map(info['Income Group'].dropna().to_dict()).fillna(df_info["Income group"])

    #same region, one spelling
    df_info["Region"] = df_info["Region"].replace({"Latin America & the Caribbean": "Latin America & Caribbean"})

    #check for missing data
    print("Missing Region data:",df_info[df_info["Region"].isnull()]["Jurisdiction covered"].values,'\n')
    print("Missing Income Group data:",df_info[df_info["Income group"].isnull()]["Jurisdiction covered"].values,'\n')

    df_info = df_info.drop_duplicates(subset="Unique ID")

    #type and subtype
    def derive_subtype(row):
        id_parts = row["Unique ID"].split("_")
        if id_parts[0] == "UND":
            return "Nacional Indeciso"
        if row["Unique ID"].startswith("ETS_EU"):
            return "Regional"
        if len(id_parts) <= 2 or row["Jurisdiction covered"] in NACIONAIS_COM_SUFIXO:
            return "Nacional"
        return "Subnacional - Município" if row["Jurisdiction covered"] in CIDADES else "Subnacional - Estado/Província"

    df_info["Subtype"] = df_info["key"].map(old["Subtype"])
    derived_subtype = df_info.apply(derive_subtype, axis=1)
    new_subtype = df_info[df_info["Subtype"].isnull()]
    print("Subtype derived from the instrument ID (new instruments, please review):")
    print(pd.DataFrame({"Instrument name": new_subtype["Instrument name"], "Subtype": derived_subtype[new_subtype.index]}).to_string(index=False), '\n')
    df_info["Subtype"] = df_info["Subtype"].fillna(derived_subtype)
    manual = df_info["key"].isin(SUBTYPE_MANUAL)
    df_info.loc[manual, "Subtype"] = df_info.loc[manual, "key"].map(SUBTYPE_MANUAL)

    df_info["Type"] = df_info["Type"].apply(lambda x: "Carbon tax" if "Carbon tax" in x else "ETS")

    #checks for missing data
    missing = df_price[~df_price['key'].isin(df_info["key"])]['Name of the initiative']
    print("Price data missing gen. information:",missing.values,'\n')

    #remove NAs
    year_cols = [c for c in df_price.columns if isinstance(c, int)]
    df_price = df_price.dropna(subset=year_cols, how="all")

    #instruments with the same name would be ambiguous in the series
    duplicated_price = df_price["Name of the initiative"].duplicated(keep=False)
    print("Price rows dropped (duplicated name):", df_price[duplicated_price]["Name of the initiative"].values, '\n')
    df_price = df_price[~duplicated_price]

    #prepare data for time series dataframe
    df_price = df_price.set_index(["Name of the initiative","Instrument Type"])[year_cols]
    df_price.columns.name="Year"
    df_price = df_price.stack().to_frame("Price")

    #REVENUE
    df_revenue = df_revenue.rename(columns={"Instrument name": "Name of the initiative", "Type": "Instrument Type"})
    rev_years = [c for c in df_revenue.columns if isinstance(c, int)]
    df_revenue = df_revenue.set_index(["Name of the initiative",'Instrument Type'])[rev_years]

    df_revenue.columns.name="Year"
    df_revenue = df_revenue.stack().to_frame("Revenue")

    #EMISSIONS
    instrument_dict = df_price.reset_index(['Instrument Type','Year'])['Instrument Type'].to_dict()
    instrument_dict.update(df_revenue.reset_index(['Instrument Type','Year'])['Instrument Type'].to_dict())

    df_emissions['Instrument Type'] = df_emissions['Name of the initiative'].map(instrument_dict)

    #fill nan values
    for i, v in df_emissions[df_emissions['Instrument Type'].isnull()].iterrows():
        if "ETS" in v['Name of the initiative']:
            df_emissions.at[i,'Instrument Type'] = "ETS"
        elif "carbon tax" in v['Name of the initiative'].lower():
            df_emissions.at[i,'Instrument Type'] = "Carbon tax"
        else:
            print(v['Name of the initiative'],"is missing instrument type")

    em_years = [c for c in df_emissions.columns if isinstance(c, int)]
    df_emissions = df_emissions.set_index(["Name of the initiative",'Instrument Type'])[em_years]
    df_emissions = df_emissions.drop("Total", errors="ignore")

    df_emissions.columns.name="Year"
    df_emissions = df_emissions.stack().to_frame("Emissions")

    series_wb = pd.concat([df_price,df_revenue,df_emissions],axis=1).reset_index()

    not_in_info = set(series_wb["Name of the initiative"].map(_norm)) - set(df_info["key"])
    print("Series names without gen. information:", sorted(not_in_info), '\n')

    #Traducoes
    df_info["Status"] = df_info["Status"].map({"Implemented":"Implementado",
                                            "Under consideration":"Em consideração",
                                            "Under development":"Em desenvolvimento",
                                            "Abolished":"Extinto"})

    df_info['Type'] = df_info['Type'].map({"Carbon tax":"Taxas de Carbono",
                                            "ETS":"Sistema  de comércio de licenças de emissão (ETS)"})


    series_wb['Instrument Type'] = series_wb['Instrument Type'].map({"Carbon tax":"Taxas de Carbono",
                                                                     "ETS":"ETS"})

    df_info = df_info.drop(columns="key")

    #concat and save time series
    series_wb.to_csv(f"{save_path}/wb_time_series.csv",
                                            index=False,sep=";",decimal=",")

    #save data info
    df_info.to_csv(f"{save_path}/wb_info.csv",
                index=False,sep=";",decimal=",")


    last_update_db.to_csv('data/update_info.csv')

    print("Done WB")


def update_wb_crediting(file_path='data/raw/dados_wb.xlsx', save_path="data/processed"):
    """
    Treat the crediting sheets of the World Bank file (crediting mechanisms and Article 6.2 agreements).

    Saves:
        wb_crediting_info.csv: one row per mechanism (description, status, cumulative credits until 31/12 of the last year).
        wb_crediting_issuance.csv: annual issuance per mechanism (long format: Mechanism;Year;Issued).
        wb_cooperative.csv: Article 6.2 agreements (Buyer;Year;Seller;Status;Notes).
    """
    last_update_db = pd.read_csv('data/update_info.csv', index_col=0)

    status_pt = {"Implemented": "Implementado", "Under development": "Em desenvolvimento",
                 "Abolished": "Extinto", "Removed": "Removido"}
    administration_pt = {"Governmental": "Governamental", "Independent": "Independente", "International": "Internacional"}
    scope_pt = {"Global": "Global", "National": "Nacional", "Subnational": "Subnacional", "Regional": "Regional"}

    #DETAIL
    detail = _read_sheet(file_path, 'Crediting_Detail', 'Mechanism')
    detail.columns = [str(c).strip() for c in detail.columns]
    detail = detail.dropna(subset=["Mechanism"])
    detail["Mechanism"] = detail["Mechanism"].str.replace("\xa0", " ").str.strip()

    unknown = detail[detail["Status"].notnull() & ~detail["Status"].isin(status_pt)]
    print("Crediting mechanisms with status outside the expected list (shown as 'Não classificado'):",
          unknown[["Mechanism", "Status"]].values.tolist(), '\n')
    detail["Status"] = detail["Status"].map(status_pt).fillna("Não classificado")
    detail["Administration"] = detail["Administration"].map(administration_pt).fillna("Não informado")
    detail["Scope"] = detail["Scope"].map(scope_pt).fillna("Não informado")

    sectors = ['Agriculture', 'CCS / CCU', 'Energy Efficiency / Fuel Switching', 'Forestry / Land Use',
               'Fugitive Emissions', 'Industrial Gases/Manufacturing', 'Renewable Energy', 'Transport', 'Waste']
    detail["Eligible sectors"] = detail[sectors].eq("Yes").apply(lambda row: ', '.join(row.index[row]), axis=1)

    cumulative = {c: c for c in detail.columns if c.startswith("Cumulative")}
    cumulative_year = re.search(r"(\d{4})", list(cumulative)[0]).group(1)
    detail = detail.rename(columns={
        "Administering Jurisdiction or organisation": "Jurisdiction",
        "Income Group of Administering Country": "Income group",
        "Compliance CPIs accepting credits generated through mechanism": "Accepted by compliance instruments",
        [c for c in cumulative if "issued" in c][0]: "Cumulative issued (kt)",
        [c for c in cumulative if "retired" in c][0]: "Cumulative retired (kt)",
        [c for c in cumulative if "cancelled" in c][0]: "Cumulative cancelled (kt)",
        [c for c in cumulative if "Projects" in c][0]: "Cumulative projects registered",
    })
    keep = ["Mechanism", "Administration", "Status", "Year of Implementation", "Scope", "Jurisdiction", "Region",
            "Income group", "Credit name", "Price (Range)", "Eligible sectors", "Accepted by compliance instruments",
            "Cumulative issued (kt)", "Cumulative retired (kt)", "Cumulative cancelled (kt)",
            "Cumulative projects registered", "Description of the mechanism", "Recent developments"]
    detail = detail[keep].replace(r"^\s*$", np.nan, regex=True)
    for col in ["Mechanism", "Credit name", "Price (Range)", "Accepted by compliance instruments"]:
        detail[col] = detail[col].str.replace("\xa0", " ").str.strip()

    #ISSUANCE
    issuance = _read_sheet(file_path, 'Crediting_Issuance', 'Mechanism')
    dropped = issuance["Mechanism"].isnull()
    print("Issuance rows without mechanism name (dropped):", int(dropped.sum()),
          "| total issued in them:", issuance[dropped].select_dtypes("number").sum().sum(), '\n')
    issuance = issuance[~dropped]
    issuance["Mechanism"] = issuance["Mechanism"].str.replace("\xa0", " ").str.strip()
    years = [c for c in issuance.columns if isinstance(c, int)]
    issuance = issuance.set_index("Mechanism")[years]
    issuance.columns.name = "Year"
    issuance = issuance.stack().to_frame("Issued").reset_index()

    no_detail = sorted(set(issuance["Mechanism"]) - set(detail["Mechanism"]))
    print("Issuance mechanisms without detail (administration unknown):", no_detail, '\n')

    #COOPERATIVE APPROACHES (Article 6.2)
    coop = _read_sheet(file_path, 'Cooperative Approaches', 'Buyer').dropna(subset=["Buyer"])
    coop = coop.rename(columns={"Year of Agreement": "Year", "Status of Agreement": "Status"})
    for col in ["Buyer", "Seller", "Status"]:
        coop[col] = coop[col].str.replace("\xa0", " ").str.strip()
    # the file spells "Bilateral" as "Bilteral" and varies the capitalisation
    coop_status_pt = {"mou signed": "Memorando de entendimento assinado",
                      "implementing agreement signed": "Acordo de implementação assinado",
                      "bilteral authorization completed": "Autorização bilateral concluída",
                      "bilateral authorization completed": "Autorização bilateral concluída"}
    coop["Status"] = coop["Status"].str.lower().map(coop_status_pt).fillna(coop["Status"])
    print("Article 6.2 agreements by status:", coop["Status"].value_counts().to_dict(), '\n')

    #update info: "Data last updated by May 1, 2026" in the first cell of each sheet
    def sheet_date(sheet):
        first = pd.read_excel(file_path, sheet_name=sheet, nrows=1, usecols=[0]).columns[0]
        return translate_date(first.replace("Data last updated by ", ""))

    last_update_db.loc['WB_CREDITO'] = sheet_date('Crediting_Detail')
    last_update_db.loc['WB_ARTIGO6'] = sheet_date('Cooperative Approaches')

    detail.to_csv(f"{save_path}/wb_crediting_info.csv", index=False, sep=";", decimal=",")
    issuance.to_csv(f"{save_path}/wb_crediting_issuance.csv", index=False, sep=";", decimal=",")
    coop.to_csv(f"{save_path}/wb_cooperative.csv", index=False, sep=";", decimal=",")
    last_update_db.to_csv('data/update_info.csv')

    print(f"Done WB crediting (cumulative values until 31/12/{cumulative_year})")


if __name__ == "__main__":
     update_wb()
     update_wb_crediting()
