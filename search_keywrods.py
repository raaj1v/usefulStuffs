import re

def search_keywords(input_text2):
    words = input_text2.split()
    cleaned_words = [word for word in words if word.lower() not in prepositions]
    output_text = ' '.join(cleaned_words)
    output_text = output_text.replace(",", " BRK").replace(".", " BRK")
    output_text = re.findall(r'[a-zA-Z]+', output_text)
    filtered_words = [word for word in output_text
                      if word.lower() not in stop_words
                      and word.lower() not in location['Districts'].str.lower().tolist()
                      and word.lower() not in procurement['ProcurementTerms'].str.lower().tolist()
                      and word.lower() not in company_df['CompanyName'].str.lower().tolist()
                      and word.lower() not in company_df['Abbrevation'].str.lower().tolist()]

    filtered_words = [shortCodes.loc[shortCodes['ShortName'].str.lower() == word.lower(), 'Fullform'].iloc[0]
                      if any(shortCodes['ShortName'].str.lower() == word.lower()) else word for word in filtered_words]

    pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, filtered_words)) + r')\b', re.IGNORECASE)
    found_phrases = pattern.findall(' '.join(filtered_words))

    ExtractedMatches = {
        'product_matches': [(match.iloc[0]['ProductCode'], phrase) for phrase in found_phrases for match in
                            [product_df.loc[product_df['ProductName'].str.lower() == phrase.lower()]] if not match.empty],
        'keyword_matches': [(match.iloc[0]['keycodeid'], phrase) for phrase in found_phrases for match in
                            [product_df.loc[product_df['keyword'].str.lower() == phrase.lower()]] if not match.empty],
        'synonym_matches': [(match.iloc[0]['synonymId'], phrase) for phrase in found_phrases for match in
                            [product_df.loc[product_df['synonymkeyword'].str.lower() == phrase.lower()]] if not match.empty]
    }

    not_found_words = [word for word in filtered_words if not any(
        [phrase == word for _, phrase in ExtractedMatches['product_matches'] + ExtractedMatches['keyword_matches'] +
         ExtractedMatches['synonym_matches']])]

    return ExtractedMatches, not_found_words


#MORE FASTTTER SEARCH
import re

def search_keywords33(input_text2):
    words = input_text2.split()
    cleaned_words = [word for word in words if word.lower() not in prepositions]
    output_text = ' '.join(cleaned_words)
    output_text = output_text.replace(",", " BRK").replace(".", " BRK")
    output_text = re.findall(r'[a-zA-Z]+', output_text)
    
    filtered_words = list(set([word for word in output_text
                      if word.lower() not in stop_words
                      and word.lower() not in location['Districts'].str.lower().tolist()
                      and word.lower() not in procurement['ProcurementTerms'].str.lower().tolist()
                      and word.lower() not in company_df['CompanyName'].str.lower().tolist()
                      and word.lower() not in company_df['Abbrevation'].str.lower().tolist()]))
    
    filtered_words = list(set([shortCodes.loc[shortCodes['ShortName'].str.lower() == word.lower(), 'Fullform'].iloc[0]
                      if any(shortCodes['ShortName'].str.lower() == word.lower()) else word for word in filtered_words]))

    pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, filtered_words)) + r')\b', re.IGNORECASE)
    found_phrases = pattern.findall(' '.join(filtered_words))

    ExtractedMatches = {
        'product_matches': list(set([(match.iloc[0]['ProductCode'], phrase) for phrase in found_phrases for match in
                            [product_df.loc[product_df['ProductName'].str.lower() == phrase.lower()]] if not match.empty])),
        'keyword_matches': list(set([(match.iloc[0]['keycodeid'], phrase) for phrase in found_phrases for match in
                            [product_df.loc[product_df['keyword'].str.lower() == phrase.lower()]] if not match.empty])),
        'synonym_matches': list(set([(match.iloc[0]['synonymId'], phrase) for phrase in found_phrases for match in
                            [product_df.loc[product_df['synonymkeyword'].str.lower() == phrase.lower()]] if not match.empty]))
    }

    not_found_words = list(set([word for word in filtered_words if not any(
        [phrase == word for _, phrase in ExtractedMatches['product_matches'] + ExtractedMatches['keyword_matches'] +
         ExtractedMatches['synonym_matches']])]))

    return ExtractedMatches, not_found_words
