import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

def fetch_report_details(ingredient_url, pbar):
    response = requests.get(ingredient_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'ContentContainer_ContentBottom_ingredientReferences'})
        
        if table:
            rows = table.find_all('tr')[1:]  # Ignore header
            reports = []
            
            for row in rows:
                cells = row.find_all('td')
                status_cell = cells[1]
                link_tag = status_cell.find('a')
                date_reference = cells[2].text.strip()
                
                if link_tag and 'report' in link_tag.text.lower():
                    report_link = link_tag['href']
                    # Check for javascript:alert links
                    if 'javascript:alert' in report_link:
                        return "null", "null", "null"
                    report_link = f"https://cir-reports.cir-safety.org/{report_link}"
                    status = link_tag.text.strip()
                    reports.append((date_reference, report_link, status))
            
            if reports:
                final_reports = [r for r in reports if 'final report' in r[2].lower()]
                published_reports = [r for r in reports if 'published report' in r[2].lower()]

                if final_reports:
                    selected_report = final_reports[0]
                elif published_reports:
                    selected_report = published_reports[0]
                else:
                    selected_report = reports[0]

                try:
                    report_date = pd.to_datetime(selected_report[0], format='%B %d, %Y')
                except ValueError:
                    try:
                        report_date = pd.to_datetime(selected_report[0], format='%Y')
                    except ValueError:
                        try:
                            report_date = pd.to_datetime(selected_report[0])
                        except ValueError:
                            report_date = pd.NaT  # Set as NaT if date is unrecognized

                pbar.update(1)
                return selected_report[1], selected_report[2], report_date if pd.notna(report_date) else "Unknown Date"
    
    pbar.update(1)
    return "null", "null", "null"

def main():
    filename = 'CIR_Ingredients_Report.csv'
    df = pd.read_csv(filename)

    if 'link' not in df.columns:
        print("La colonna 'link' non esiste nel file CSV.")
        return

    with tqdm(total=min(790, len(df) - 7000)) as pbar:
        report_links = []
        statuses = []
        date_references = []

        for link in df['link'][7000:7790]:
            report_link, status, date_reference = fetch_report_details(link, pbar)
            report_links.append(report_link)
            statuses.append(status)
            date_references.append(date_reference)

    df.loc[7000:7789, 'Link del report'] = report_links # Per le righe dal 7000 al 7789
    df.loc[7000:7789, 'Stato'] = statuses
    df.loc[7000:7789, 'Data/Referenza'] = date_references

    df.to_csv(filename, index=False)
    print("File CSV aggiornato con successo!")

if __name__ == "__main__":
    main()
