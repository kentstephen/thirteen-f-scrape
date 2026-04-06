"""Top 50 institutional 13F filers.

CIK is the primary key — EDGAR entity names are inconsistent,
so we maintain our own display names here.
"""

FUNDS: dict[str, str] = {
    # Mega asset managers
    "BlackRock": "1364742",
    "Vanguard Group": "102909",
    "State Street": "93751",
    "Fidelity Management": "315066",
    "JPMorgan Chase": "19617",
    "Goldman Sachs": "886982",
    "Morgan Stanley": "895421",
    "Wellington Management": "902219",
    # Large multi-strategy hedge funds
    "Berkshire Hathaway": "1067983",
    "Citadel Advisors": "1423053",
    "DE Shaw": "1009207",
    "Two Sigma Investments": "1179392",
    "Millennium Management": "1273087",
    "Point72 Asset Management": "1603466",
    "Bridgewater Associates": "1350694",
    "AQR Capital Management": "1167557",
    "Balyasny Asset Management": "1218710",
    "Schonfeld Strategic Advisors": "1665241",
    # Quant / systematic
    "Renaissance Technologies": "1037389",
    # Activist / high-conviction
    "Pershing Square": "1336528",
    "Elliott Investment Management": "1048445",
    "Third Point": "1040273",
    "ValueAct Capital": "1351069",
    "Icahn Capital": "921669",
    "Starboard Value": "1517137",
    "Trian Fund Management": "1345471",
    # Tiger cubs / tech-focused
    "Tiger Global": "1167483",
    "Coatue Management": "1135730",
    "Lone Pine Capital": "1061165",
    "Viking Global Investors": "1103804",
    "Whale Rock Capital": "1387322",
    "Alkeon Capital Management": "1230239",
    # Macro / global
    "Duquesne Family Office": "1536411",
    "Appaloosa Management": "1656456",
    "Greenlight Capital": "1079114",
    "Soros Fund Management": "1029160",
    "Baupost Group": "1061768",
    "Tudor Investment Corp": "923093",
    # Value / special situations
    "Scion Asset Management": "1649339",
    "Oaktree Capital Management": "949509",
    "Dodge & Cox": "200726",
    # PE / alternative
    "Apollo Management": "1449434",
    "KKR": "1399770",
    # Healthcare
    "Baker Brothers Advisors": "1263508",
    # ARK / thematic
    "ARK Invest": "1697855",
    # Sovereign wealth / pensions / foundations
    "Norges Bank (Norway)": "1374170",
    "Bill & Melinda Gates Foundation": "1166559",
    "Temasek Holdings": "1583984",
    # Additional to reach 50
    "Farallon Capital": "1044715",
    "Davidson Kempner Capital": "1040971",
}
