import pandas as pd
import re
import nltk
nltk.download('wordnet')
from nltk import WordNetLemmatizer
from difflib import get_close_matches
import streamlit as st
import pyodbc
import math
import json



server = '192.168.100.126'
database = 'Python'
username = 'Rajeev'
password = 'rajeev@123'
driver = '{ODBC Driver 17 for SQL Server}'

conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')
cursor=conn.cursor()

uom = pd.read_sql("SELECT * FROM uom_5052023", conn)
location = pd.read_sql("SELECT * FROM indianLocation5052023", conn)
prepositions = pd.read_sql("SELECT * FROM prepositionsFinal5052023", conn)['Preposition'].tolist()
shortCodes = pd.read_sql("SELECT * FROM shortCodesProduct_5052023", conn)
procurement = pd.read_sql("SELECT * FROM PT_5052023", conn)
product_df = pd.read_sql("SELECT * FROM keywordProductSynonym_5052023", conn)
product_df['synonymkeyword'] = product_df['synonymkeyword'].fillna('')
company_df = pd.read_sql("SELECT * FROM company_list_5052023", conn)
stop_words = pd.read_sql("SELECT * FROM stopWordsFinal_5052023", conn)["Stop word"].tolist()



#=====================================================================================================================================

def textSegmentation(input_text):
    input_text = re.findall(r'[a-zA-Z]+', input_text)
    result_dict={}
    units = set()
    for word in input_text:
        if any(uom['units'].str.contains(fr"\b{word}\b", case=False, regex=True)):
            units.add(word)
    result_dict['units'] = units
   
    locations = set()

    # Check for each word in the input text
    # for word in input_text:
    #     matching_locations = location[location['Districts'].str.lower() == word.lower()]['Districts']
    #     locations.update(matching_locations)

    # result_dict['locations'] = locations

    procurementTerm = set()
    for word in input_text:
        matchingProcurmentTerm = procurement[procurement['PTerms'].str.lower() == word.lower()]['PTerms']
        procurementTerm.update(matchingProcurmentTerm)
    result_dict['PTerms'] = procurementTerm   
    return result_dict
#=====================================================================================================================================

def match_company(input_text):
    input_words = re.findall(r'[a-zA-Z,]+', input_text)
    # initialize variables
    companyDict = {}
    keyword_matches = []
    remaining_words = input_words
    # search for longest possible matching word strings in keyword column
    while len(remaining_words) > 0:
        for i in range(len(remaining_words), 0, -1):
            phrase = ' '.join(remaining_words[:i])
            matches = company_df[company_df['Abbrevation'].str.lower() == phrase.lower()]
            if len(matches) > 0:
                keyword_matches.append((matches.iloc[0]['companyrecno'], phrase))
                remaining_words = remaining_words[i:]
                break
        else:
            for i in range(len(remaining_words), 0, -1):
                phrase = ' '.join(remaining_words[:i])
                matches = company_df[company_df['CompanyName'].str.lower() == phrase.lower()]
                if len(matches) > 0:
                    keyword_matches.append((matches.iloc[0]['companyrecno'], phrase))
                    remaining_words = remaining_words[i:]
                    break
            else:
                # no match found in any column
                remaining_words.pop(0)
    companyDict['company_matches'] = keyword_matches
    # return keycodeids and corresponding phrases
    return companyDict

 #=====================================================================================================================================
def search_keywords(input_text2):
    words = input_text2.split()
    cleaned_words = []
    for i in range(len(words)):
        if words[i].lower() in prepositions:
            break
        cleaned_words.append(words[i])
    output_text = ' '.join(cleaned_words)
    # print("output_text", output_text)
    # remove unwanted characters
    output_text = output_text.replace(",", " BRK").replace(".", " BRK")
    output_text = re.findall(r'[a-zA-Z]+', output_text)
    # remove stop words
    filtered_words = [word for word in output_text 
                  if word.lower() not in stop_words]
                #   and word.lower() not in location['Districts'].str.lower().tolist()
                #   and word.lower() not in procurement['PTerms'].str.lower().tolist()
                #   and word.lower() not in company_df['CompanyName'].str.lower().tolist()
                #   and word.lower() not in company_df['Abbrevation'].str.lower().tolist()]
    # print("filtered_words", filtered_words)

    for i in range(len(filtered_words)):
        for j in range(len(shortCodes)):
            if filtered_words[i].lower() == shortCodes['ShortName'][j].lower():
                filtered_words[i] = shortCodes['Fullform'][j]
                filtered_words
        # print("filtered_words2", filtered_words)

    # initialize variables
    ExtractedMatches=[]
    keyword_matches = []
    product_matches = []
    synonym_matches = []
    remaining_words = filtered_words
    wordNotFound=[]
    # search for longest possible matching word strings in keyword column
    while len(remaining_words) > 0:
        for i in range(len(remaining_words), 0, -1):
            phrase = ' '.join(remaining_words[:i])
            matches = product_df[product_df['ProductName'].str.lower() == phrase.lower()]
            if len(matches) > 0:
                product_matches.append((matches.iloc[0]['ProductCode'])) #, phrase
                remaining_words = remaining_words[i:]
                break
        else:
            # no match found in keyword column, try synonym column
            for i in range(len(remaining_words), 0, -1):
                phrase = ' '.join(remaining_words[:i])
                matches = product_df[product_df['keyword'].str.lower()==phrase.lower()]
                if len(matches) > 0:
                    keyword_matches.append((matches.iloc[0]['keycodeid'])) #, phrase
                    remaining_words = remaining_words[i:]
                    break
            else:
                # no match found in synonym column, try productname column
                for i in range(len(remaining_words), 0, -1):
                    phrase = ' '.join(remaining_words[:i])
                    matches = product_df[product_df['synonymkeyword'].str.lower()==phrase.lower()]
                    if len(matches) > 0:
                        synonym_matches.append((matches.iloc[0]['synonymId']))  #, phrase
                        remaining_words = remaining_words[i:]
                        break
                else:
                    # no match found in any column
                    wordNotFound.append(remaining_words.pop(0))

    ExtractedMatches=[keyword_matches, product_matches, synonym_matches]
    # return keycodeids and corresponding phrases
    return ExtractedMatches,  wordNotFound


 #=====================================================================================================================================

def final(input_text):
    comp = match_company(input_text)
    text_segments = textSegmentation(input_text)

    lemmatizer = WordNetLemmatizer()
    not_found_words = search_keywords(input_text)[1]

    lemmatized_words = ' '.join(lemmatizer.lemmatize(word) for word in not_found_words)
    not_found_lemmatized = search_keywords(lemmatized_words)[1]

    close_matches = []
    for word in not_found_lemmatized:
        word_close_matches = [
            match for match in get_close_matches(word, product_df['keyword'], n=2, cutoff=0.8)
            if match[0].lower() == word[0].lower()
        ]
        close_matches.extend(word_close_matches)

    brahmastra = ' '.join(close_matches)
    code_a, code_b, code_d = search_keywords(input_text)[0], search_keywords(lemmatized_words)[0], search_keywords(brahmastra)[0]
    print(type(code_a))

    return code_a, code_b, code_d, comp, text_segments


##\WORKING function for complete search
cursor.execute("select AITenderid, [AIChunkid], [ChunkText] from Chunk")
Secondrows = cursor.fetchall()

secdf = pd.DataFrame( [[ij for ij in i] for i in Secondrows] )
secdf.rename(columns={0: 'AITenderId', 1: 'AIChunkid', 2: 'ChunkText'}, inplace=True)
print('columns names:',secdf.columns.tolist())


for m, i, j in zip(secdf['AITenderId'], secdf['AIChunkid'], secdf['ChunkText']):
    print(m, i, j)
    search = final(j)
    print('Main Search:',search)
    
    # Get the last list of strings
    productsearch = search[0]
    # print('Main Search after Product :',productsearch[0])
    product_matches= search[0][0]
    keyword_matches= search[2][1]
    synonym_matches= search[1][2]

    company_matches= search[3].get('company_matches')
    
    units= search[4].get('units')

    procurement_terms= search[4].get('PTerms')


    for product_match in product_matches:
        if not (isinstance(product_match, float) and math.isnan(product_match)):
            product_match_str = int(product_match)
            cursor.execute("INSERT INTO [dbo].[Classification_real] (AIChunkId, Products_matches) VALUES (?, ?)", (i, product_match_str))
            cursor.commit()

    # For keyword matches
    for keyword_match in keyword_matches:
        if not (isinstance(keyword_match, float) and math.isnan(keyword_match)):
            keyword_match_str = int(keyword_match)
            cursor.execute("INSERT INTO [dbo].[Classification_real] (AIChunkId, keywords_matches) VALUES (?, ?)", (i, keyword_match_str))
            cursor.commit()

    # For synonym matches
    for synonym_match in synonym_matches:
        if not (isinstance(synonym_match, float) and math.isnan(synonym_match)):
            synonym_match_str = int(synonym_match)
            cursor.execute("INSERT INTO [dbo].[Classification_real] (AIChunkId, synonyms_matches) VALUES (?, ?)", (i, synonym_match_str))
            cursor.commit()

    for unit in units:
        unit_str = str(unit)
        cursor.execute("INSERT INTO [dbo].[Classification_real] (AIChunkId, units) VALUES (?, ?)", (i, unit_str))
        cursor.commit()
    # for location in locations:
    #     location_str = str(location)
    #     cursor.execute("INSERT INTO [dbo].[Classification_real] (AIChunkId, locations) VALUES (?, ?)", (i, location_str))
    #     cursor.commit()
    for procurement_term in procurement_terms:
        procurement_term_str = str(procurement_term)
        cursor.execute("INSERT INTO [dbo].[Classification_real] (AIChunkId, PTerms) VALUES (?, ?)", (i, procurement_term_str))
        cursor.commit()