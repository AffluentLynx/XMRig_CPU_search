import tqdm
import time
import requests
import urllib.parse

CPU = "AMD Ryzen 9 5950X 16-Core Processor"
TARGET_RAM = "F4-4000C18D-32GVK"

URL = "https://api.xmrig.com/1/benchmark"

def fetch_benchmarks():
    """
    Fetches the benchmark data from the API and returns the JSON response.
    """
    response = requests.get(URL + 's?cpu=' + urllib.parse.quote_plus(CPU))
    return response.json()

def get_ram_info(benchmarks):
    """
    Fetches the benchmark data for the specified RAM model from the xmrig.com API.
    
    Args:
        benchmarks (list): A list of dictionaries containing benchmark data.
        
    Returns:
        list: A list of dictionaries containing benchmark data with RAM information.
    """
    ram_info_list = []
    benchmarks=benchmarks[1950:2050] #limit the search
    
    for benchmark in tqdm.tqdm(benchmarks, desc="Processing benchmarks", unit="benchmark"):
        time.sleep(2)
        benchmark_id = benchmark.get("id")
        if benchmark_id:
            uri = URL + '/' + benchmark_id
            response = requests.get(uri)
            if response.status_code == 200:
                benchmark_data = response.json()
                # print(benchmark_data)
                if benchmark_data["dmi"] == None:
                    print(f'Error requesting benchmark ID: {benchmark_data['id']}')
                    continue
                for dimm in benchmark_data["dmi"]["memory"]:
                    if dimm.get("product") == TARGET_RAM:
                        ram_info_list.append(benchmark_data)
                        break
    return ram_info_list


def get_top_benchmarks(filtered_benchmarks):
    """
    Sorts the filtered benchmarks by performance and returns the top 5 results.
    """
    sorted_benchmarks = sorted(filtered_benchmarks, key=lambda x: x["performance"], reverse=True)
    return sorted_benchmarks[:5]

def main():
    benchmarks = fetch_benchmarks()
    filtered_benchmarks = get_ram_info(benchmarks)
    input(filtered_benchmarks)
    top_benchmarks = get_top_benchmarks(filtered_benchmarks)
    
    for benchmark in top_benchmarks:
        print(f"Performance: {benchmark['performance']}")
        print(f"RAM Model: {benchmark['ram_model']}")
        print(f"Timings: {benchmark['ram_timings']}")
        print("---")

if __name__ == "__main__":
    main()