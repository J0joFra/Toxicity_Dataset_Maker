import requests
from PyPDF2 import PdfReader
import io
import re
import pandas as pd

def extract_text_from_pdf_url(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        
        file_stream = io.BytesIO(response.content)
        pdf_reader = PdfReader(file_stream)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving PDF: {e}")
        return None
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None

def extract_values(text):
    # Define regular expressions for NOAEL and LD50
    ld50_pattern = re.compile(r'LD50\s*>\s*(\d+(\.\d+)?\s*\w+/kg)', re.IGNORECASE)
    noael_pattern = re.compile(r'NOAEL\s*>\s*(\d+(\.\d+)?\s*\w+/kg)', re.IGNORECASE)

    # Find all matches in the text
    ld50_matches = ld50_pattern.findall(text)
    noael_matches = noael_pattern.findall(text)

    # Initialize species dictionaries
    species_ld50 = {'rabbit': [], 'mouse': [], 'rat': []}
    species_noael = {'rabbit': [], 'mouse': [], 'rat': []}

    # Check for matches and assign to appropriate species
    for match in ld50_matches:
        value = match[0].strip()
        if re.search(r'\brabbit\b', text, re.IGNORECASE):
            species_ld50['rabbit'].append(value)
        elif re.search(r'\bmouse\b', text, re.IGNORECASE):
            species_ld50['mouse'].append(value)
        elif re.search(r'\brat\b', text, re.IGNORECASE):
            species_ld50['rat'].append(value)

    for match in noael_matches:
        value = match[0].strip()
        if re.search(r'\brabbit\b', text, re.IGNORECASE):
            species_noael['rabbit'].append(value)
        elif re.search(r'\bmouse\b', text, re.IGNORECASE):
            species_noael['mouse'].append(value)
        elif re.search(r'\brat\b', text, re.IGNORECASE):
            species_noael['rat'].append(value)

    return species_ld50, species_noael

# Read the Excel file
excel_file = r"C:\Users\JoaquimFrancalanci\OneDrive - ITS Angelo Rizzoli\Desktop\Progetti\Project Work\CIR_Ingredients_Report.xlsx"
df = pd.read_excel(excel_file)

# Iterate over each row in the dataframe
for index, row in df.iterrows():
    pdf_url = row['Link del report']
    if pd.notna(pdf_url):  # Check if the URL is not NaN
        pdf_text = extract_text_from_pdf_url(pdf_url)
        
        if pdf_text:
            ld50_values, noael_values = extract_values(pdf_text)
            
            # Update dataframe with extracted values
            df.at[index, 'LD50 Rabbit'] = ', '.join(ld50_values['rabbit'])
            df.at[index, 'LD50 Mouse'] = ', '.join(ld50_values['mouse'])
            df.at[index, 'LD50 Rat'] = ', '.join(ld50_values['rat'])
            
            df.at[index, 'NOAEL Rabbit'] = ', '.join(noael_values['rabbit'])
            df.at[index, 'NOAEL Mouse'] = ', '.join(noael_values['mouse'])
            df.at[index, 'NOAEL Rat'] = ', '.join(noael_values['rat'])
        else:
            print(f"Failed to retrieve or parse PDF from URL: {pdf_url}")

# Save updated dataframe back to Excel
df.to_excel(excel_file, index=False)
print("Extraction and update completed successfully.")
