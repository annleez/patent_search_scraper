from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, re, sys, csv
from typing import Set, List, Any

def get_bool_query(first_term: str, second_term: str, acronym = "") -> str:
    # Transform query from "dslr camera, digital single lens reflex camera"
    # -> (dslr OR digital single lens reflex) AND camera
    if acronym == "" or acronym == first_term or acronym == second_term: # handle two-term input w/o overlap
        return f"{first_term} OR {second_term}"
    
    ''' right now this only works for pretty simple cases where acronym
    is at the beginning or end of either term... since we don't
    have an acronym identification/diambiguation system yet
    '''
    if first_term.find(acronym) != -1: # acronym in first term
        overlap = first_term.replace(acronym, "").strip()
        definition = (second_term.replace(overlap, "")).strip()
    elif second_term.find(acronym) != -1: # acronym in second term
        overlap = second_term.replace(acronym, "").strip()
        definition = (first_term.replace(overlap, "")).strip()
    else: # acronym not found
        return ""
    
    return f"({acronym} OR {definition}) AND {overlap}"

def transform_query_to_url(query: str) -> str:
    """
    Transform query to this format: "dslr camera" -> "(dslr+camera)"
    For multi-term queries: "cats, dogs" -> "(cats%2c+dogs)"
    """
    transformed_query = (query.replace(" ", "+")).replace(",", "%2c")
    transformed_query = "(" + transformed_query + ")"
    url = "https://patents.google.com/?q=" + transformed_query
    return url

# returns format: [total number of results, top 10 results]
def scrape_patents(query: str) -> List[Any]:
    # scrape Google Patent search results
    # Selenium tutorial: https://medium.com/analytics-vidhya/web-scraping-google-search-results-with-selenium-and-beautifulsoup-4c534817ad88
    patent_ids = set() # set to hold patent ids
    option = webdriver.ChromeOptions()
    option.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
    url = transform_query_to_url(query)
    driver.get(url)
    time.sleep(2) # let results load
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # with open("soup.py", 'w', newline='') as file:
    #     file.write(soup.prettify())
    # file.close()

    # grab total number of results
    num_results_span = soup.find(id='numResultsLabel')
    num_results_text = num_results_span.get_text(strip=True)
    num_results = int(''.join(filter(str.isdigit, num_results_text)))
    
    # grab patent ID for top ten results
    result_titles = soup.find_all(class_='result-title')
    for title in result_titles:
        patent = title.get('data-result') # ex. patent/JP4406937B2/en
        patent_parts = re.split('/', patent) # "patent", patent ID, language (ex. en)
        patent_ids.add(patent_parts[1])
    assert(len(patent_ids) == 10), "ERROR: search must have at least 10 results"

    driver.quit()
    return [num_results,patent_ids]

def get_distances(term1_results: Set[str], term2_results: Set[str], both_results: Set[str]) -> List[int]:
    def jaccard_distance(set1, set2):
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return 1 - (intersection / union)

    def dice_distance(set1, set2):
        intersection = len(set1.intersection(set2))
        sorensen_dice_coeff = (2.0 * intersection) / (len(set1) + len(set2))
        return 1 - sorensen_dice_coeff

    distances = []

    # Jaccard distances: treats all elements equally
    # Dice distances: prefers overlapping elements (considers order)
    distances.append(jaccard_distance(term1_results, term2_results))
    distances.append(dice_distance(term1_results, term2_results))
    if both_results != None:
        distances.append(jaccard_distance(term1_results, both_results))
        distances.append(dice_distance(term1_results, both_results))
        distances.append(jaccard_distance(term2_results, both_results))
        distances.append(dice_distance(term2_results, both_results))
    
    return distances

if __name__ == "__main__":
    csv_file_path = 'output.csv'

    if len(sys.argv) == 1:
        query = input("Enter your query: ")
        queries = [query]
        
    elif len(sys.argv) <= 3:
        input_file = sys.argv[1]
        with open(input_file, 'r') as file:
            file_contents = file.read()
        queries = file_contents.splitlines()
        file.close()

        # change to user-specified output path
        if len(sys.argv) == 3:
            csv_file_path = sys.argv[2]
            assert(csv_file_path.endswith(".csv")), "ERROR: output file must end with '.csv'"

    else:
        print("ERROR: see readme for intended usage")
        sys.exit()

    # write output to csv
    headers = [
        "Term 1", "Term 1: total results", "Term 1: top results",
        "Term 2", "Term 2: total results", "Term 2: top results",
        "Bool term", "Bool term: total results", "Bool term: top results",
        "Jaccard distance (Term 1, Term 2)", "Dice distance (Term 1, Term 2)", "Jaccard distance (Term 1, Bool term)", "Dice distance (Term 1, Bool term)", "Jaccard distance (Term 2, Bool term)", "Dice distance (Term 2, Bool term)"]
    with open(csv_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
    file.close()

    with open(csv_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        for query in queries:
            this_row = []

            # handle query with 1 or 2 terms
            results = [] # hold sets of search results for both terms, term 1, term 2
            query_terms = re.split(r',\s*', query) # split by commas, ignoring spaces immediately after commas
            assert(len(query_terms) <= 3), "ERROR: must query by 1-3 comma-separated terms at a time"

            # search by acronym and definition individually
            for i in range(2):
                this_row.append(query_terms[i])
                search_results = scrape_patents(query_terms[i])
                results.append(search_results[1])
                this_row += search_results

            # search by all Boolean combination of terms
            # (acronym OR definition) ... AND rest of term, if applicable
            # ex. (dslr OR digital single lens reflex) AND camera
            if len(query_terms) == 3: # yes, acronym input
                bool_query = get_bool_query(query_terms[0], query_terms[1], query_terms[2])
            else:
                bool_query = get_bool_query(query_terms[0], query_terms[1])
            if bool_query != "":
                this_row.append(bool_query) # include bool query string in output as sanity check
                search_results = scrape_patents(bool_query)
                results.append(search_results[1]) #  will analyze top 10 results
                this_row += search_results # log number of total results & top 10 results
            else:
                results.append(None)
                this_row.append(["","",""])
            
            # conduct distance analysis if we have 2 terms
            if len(results) == 3:
                this_row += get_distances(results[0], results[1], results[2])
            
            writer.writerow(this_row)

    print(f"Output saved to {csv_file_path}")
    file.close()