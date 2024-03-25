from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import re, sys, csv, time
from typing import Set, List, Any
import pdb # debugging
from scraper import get_bool_queries, get_distances

def scrape_uspto(driver, query: str) -> List[Any]:
    num_results = 0
    patent_ids = set() # set to hold patent ids
    print(f"Searching USPTO: {query}")
    action_chains = ActionChains(driver)

    with open("soup.py", 'w', newline='') as file:
        driver.get('https://ppubs.uspto.gov/pubwebapp/')
        
        WebDriverWait(driver, 10).until( # let webpage load
            expected_conditions.presence_of_element_located((By.ID, "search-btn-search"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        file.write(soup.prettify())

        start_search_button = driver.find_element(By.ID, "search-tab")
        start_search_button.click()

        trix_editor = driver.find_element(By.XPATH, "//trix-editor")
        trix_editor.clear()
        trix_editor.send_keys(query)

        time.sleep(2) # avoid "too many requests"
        WebDriverWait(driver, 10).until(
            expected_conditions.element_to_be_clickable((By.ID, "search-btn-search"))
        )
        
        search_button = driver.find_element(By.ID, "search-btn-search")
        search_button.click()

        time.sleep(2) # avoid "too many requests"
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, "results-key-cntrl"))
        )

        draggable_pane = driver.find_element(By.CSS_SELECTOR, 'div.zone.ui-layout-center.ui-layout-pane.ui-layout-pane-center')
        action_chains.drag_and_drop_by_offset(draggable_pane, 0, -300).perform()

        time.sleep(2) # avoid "too many requests"

        scroll_div = driver.find_element(By.CLASS_NAME, 'slick-viewport')
        driver.execute_script("arguments[0].scrollTop = 140;", scroll_div)

        file.seek(0)
        file.truncate(0) # clear last writing
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        file.write(soup.prettify())
        
        time.sleep(2) # avoid "too many requests"

        num_results_div = driver.find_element(By.CLASS_NAME, 'resultNumber')
        num_results = num_results_div.text.strip()

        result_ids = soup.find_all(class_='sr-only', attrs={'for': lambda x: x and x.startswith('select-result-')})
        
        # print("result_ids:", result_ids)
        for i in range(30):
            id = result_ids[i]
            patent_ids.add(id.text.strip())
        
    file.close()

    return [num_results, patent_ids]

if __name__ == "__main__":
    csv_file_path = 'output/uspto_output.csv' # folder for output

    if len(sys.argv) == 1:
        query = input("Enter your query: ")
        queries = [query]

    elif len(sys.argv) > 3:
        print("ERROR: see readme for intended usage")
        sys.exit()
        
    else: # 2 or 3 arguments
        input_file = sys.argv[1]
        with open(input_file, 'r') as file:
            file_contents = file.read()
        queries = file_contents.splitlines()
        file.close()

        # change to user-specified output path
        if len(sys.argv) == 3:
            csv_file_path = 'output/' + sys.argv[2]
            assert(csv_file_path.endswith(".csv")), "ERROR: output file must end with '.csv'"

    # write output to csv
    headers = [
        "Term 1", "Term 1: total results", "Term 1: top results",
        "Term 2", "Term 2: total results", "Term 2: top results",
        "OR term", "OR term: total results", "OR term: top results",
        "AND term", "AND term: total results", "AND term: top results",
        "Jaccard distance (Term 1, Term 2)", "Dice distance (Term 1, Term 2)", "Jaccard distance (Term 1, OR term)", "Dice distance (Term 1, OR term)", "Jaccard distance (Term 2, OR term)", "Dice distance (Term 2, OR term)", "Jaccard distance (Term 1, AND term)", "Dice distance (Term 1, AND term)", "Jaccard distance (Term 2, AND term)", "Dice distance (Term 2, AND term)"]
    with open(csv_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
    file.close()

    # create web driver instance
    option = webdriver.ChromeOptions()
    # option.add_argument("--headless")
    option.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    option.add_argument("--disable-popup-blocking")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)

    with open(csv_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        for query in queries:
            this_row = []

            # handle query with 1 or 2 terms
            results = [] # hold sets of search results for both terms, term 1, term 2
            query_terms = re.split(r',\s*', query) # split by commas, ignoring spaces immediately after commas
            assert(len(query_terms) <= 3), "ERROR: must query by 1-3 comma-separated terms at a time"

            # search by acronym and definition individually
            for i in range(min(2, len(query_terms))):
                this_row.append(query_terms[i])
                scraper_results = scrape_uspto(driver, query_terms[i])
                results.append(scraper_results[1]) # will analyze top 10 results
                this_row += scraper_results

            # search by all Boolean combination of terms
            # (acronym OR definition) ... AND rest of term, if applicable
            or_query = ""
            and_query = ""
            if len(query_terms) == 3: # yes, acronym input
                or_query = get_bool_queries(query_terms[0], query_terms[1], query_terms[2])[0]
                and_query = get_bool_queries(query_terms[0], query_terms[1], query_terms[2])[1]
            elif len(query_terms) == 2:
                or_query = get_bool_queries(query_terms[0], query_terms[1])[0]
                and_query = get_bool_queries(query_terms[0], query_terms[1])[1]
                
            # ex. (dslr OR digital single lens reflex) AND camera
            if or_query != "":
                this_row.append(or_query) # include bool query string in output as sanity check
                scraper_results = scrape_uspto(driver, or_query)
                results.append(scraper_results[1])
                this_row += scraper_results
            else:
                results.append(None)
                this_row.extend(['','',''])

            # ex. (dslr AND digital single lens reflex) AND camera
            if and_query != "":
                this_row.append(and_query) # include bool query string in output as sanity check
                scraper_results = scrape_uspto(driver, and_query)
                results.append(scraper_results[1])
                this_row += scraper_results
            else:
                results.append(None)
                this_row.extend(['','',''])
            
            # conduct distance analysis if we have enough terms
            if len(results) >= 3:
                this_row += get_distances(results[0], results[1], results[2], results[3])
            
            writer.writerow(this_row)

    print(f"Output saved to {csv_file_path}")
    file.close()
    driver.quit()