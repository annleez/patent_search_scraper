from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, re, sys, csv
from typing import Set, List

def transform_query_to_url(query: str) -> str:
    """
    Transform query to this format: "dslr camera" -> "(dslr+camera)"
    For multi-term queries: "dslr camera,digital single lens reflex camera" -> "(dslr+camera%2cdigital+single+lens+reflex+camera)"
    """
    transformed_query = (query.replace(" ", "+")).replace(",", "%2c")
    transformed_query = "(" + transformed_query + ")"
    url = "https://patents.google.com/?q=" + transformed_query
    return url

def scrape_patents(query: str):
    # Scrape Google Patent search results
    # Selenium tutorial: https://medium.com/analytics-vidhya/web-scraping-google-search-results-with-selenium-and-beautifulsoup-4c534817ad88
    patent_ids = set() # set to hold patent ids
    option = webdriver.ChromeOptions()
    option.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
    url = transform_query_to_url(query)
    driver.get(url)
    time.sleep(2) # let results load
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # For top ten results, gather patent name and ID
    result_titles = soup.find_all(class_='result-title')
    for title in result_titles:
        patent = title.get('data-result') # ex. patent/JP4406937B2/en
        patent_parts = re.split('/', patent) # "patent", patent ID, language (ex. en)
        patent_ids.add(patent_parts[1])
    assert(len(patent_ids) == 10), "ERROR: search must have at least 10 results"

    driver.quit()
    return patent_ids

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
    distances.append(jaccard_distance(term1_results, term2_results))
    distances.append(jaccard_distance(term1_results, both_results))
    distances.append(jaccard_distance(term2_results, both_results))

    # Dice distances: prefers overlapping elements (considers order)
    distances.append(dice_distance(term1_results, term2_results))
    distances.append(dice_distance(term1_results, both_results))
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
        "Both terms", "Both terms: results",
        "Term 1", "Term 1: results",
        "Term 2", "Term 2: results",
        "Jaccard distance (Term 1, Term 2)", "Jaccard distance (Term 1, Both terms)", "Jaccard distance (Term 2, Both terms)", "Dice distance (Term 1, Term 2)", "Dice distance (Term 1, Both terms)", "Dice distance (Term 2, Both terms)"]
    with open(csv_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
    file.close()

    with open(csv_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        for query in queries:
            this_row = [query]

            # handle query with 1 or 2 terms
            results = [] # hold sets of search results for both terms, term 1, term 2
            query_terms = re.split(r',\s*', query) # split by commas, ignoring spaces immediately after commas
            assert(len(query_terms) <= 2), "ERROR: must query by 1 or 2 comma-separated terms at a time"

            # search by all query terms together
            search_results = scrape_patents(query)
            results.append(search_results)
            this_row.append(search_results)

            # search by acronym and definition individually
            for term in query_terms:
                this_row.append(term)
                search_results = scrape_patents(term)
                results.append(search_results)
                this_row.append(search_results)

            # conduct distance analysis if 2 terms
            if len(query_terms) == 2:
                this_row += get_distances(results[1], results[2], results[0])
            
            writer.writerow(this_row)

    print(f"Output saved to {csv_file_path}")
    file.close()