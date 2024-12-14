
import os
import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import requests  

def validate_file(file_name):
    if not file_name.endswith(".csv"):
        print("Error: The file must be a CSV.")
        sys.exit(1)
    
    if not os.path.exists(file_name):
        print("Error: The file does not exist.")
        sys.exit(1)

    try:
        return pd.read_csv(file_name, encoding='ISO-8859-1') 
    except UnicodeDecodeError:
        print("Error: Unable to decode the file with ISO-8859-1 encoding.")
        sys.exit(1)


def handle_missing_values(df):
    missing_data = df.isnull().sum()
    print(f"Missing values per column:\n{missing_data}")
    numeric_df = df.select_dtypes(include=[np.number])
    df[numeric_df.columns] = numeric_df.fillna(numeric_df.mean())
    return df


def summary_statistics(df):
    return df.describe()


def detect_outliers(df):
    numeric_df = df.select_dtypes(include=[np.number])
    z_scores = np.abs((numeric_df - numeric_df.mean()) / numeric_df.std())
    outliers = (z_scores > 3).sum()  
    return outliers


def correlation_matrix(df, output_dir):
    numeric_df = df.select_dtypes(include=[np.number])
    corr_matrix = numeric_df.corr()
    plt.figure(figsize=(10, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
    plt.savefig(os.path.join(output_dir, 'correlation_heatmap.png'))
    plt.close()
    return corr_matrix


def plot_histogram(df, column_name, output_dir):
    if column_name not in df.select_dtypes(include=[np.number]).columns:
        print(f"Warning: {column_name} is not numeric. Skipping histogram.")
        return
    plt.figure(figsize=(10, 6))
    sns.histplot(df[column_name], kde=True, bins=30)
    plt.title(f'Distribution of {column_name}')
    plt.xlabel(column_name)
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(output_dir, f'{column_name}_histogram.png'))
    plt.close()


def analyze_with_llm(data_summary, chart_files):
   
    api_proxy_base_url = "https://aiproxy.sanand.workers.dev"
    proxy_url = f"{api_proxy_base_url}/openai/v1/chat/completions"
    api_token = os.environ.get("AIPROXY_TOKEN") 

    prompt = f"""
    Data Summary:
    {data_summary}
    
    Please provide a comprehensive analysis of the dataset.
    Include insights from the correlation matrix, outliers, and any potential trends.
    Charts: {', '.join(chart_files)}
    """

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a data analysis assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        response = requests.post(proxy_url, json=payload, headers=headers)
        response.raise_for_status() 
        analysis = response.json()  
        return analysis.get('choices', [{}])[0].get('message', {}).get('content', 'Failed to generate analysis from proxy.')
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return "Failed to generate analysis from proxy."


def create_markdown_story(llm_response, output_dir):
    with open(os.path.join(output_dir, 'README.md'), 'w') as file:
        file.write("# Data Analysis Report\n\n")
        file.write("### Overview of the Dataset\n\n")
        file.write("The dataset contains various columns. Below is the summary of the dataset analysis.\n\n")
        file.write(f"### Analysis Insights\n\n{llm_response}\n")
        file.write("### Visualizations\n\n")
        file.write("![Correlation Matrix](correlation_heatmap.png)\n")
        file.write("Other visualizations are included in the charts generated.\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py dataset.csv")
        sys.exit(1)

    file_name = sys.argv[1]
    
    dataset_name = os.path.splitext(os.path.basename(file_name))[0]  
    output_dir = os.path.join(os.getcwd(), dataset_name) 
    
    os.makedirs(output_dir, exist_ok=True)
    
    df = validate_file(file_name)

    df = handle_missing_values(df)

    summary = summary_statistics(df)
    outliers = detect_outliers(df)
    corr_matrix = correlation_matrix(df, output_dir)

    plot_histogram(df, df.columns[0], output_dir)

    data_summary = f"Summary statistics:\n{summary}\nOutliers detected:\n{outliers}"
    llm_response = analyze_with_llm(data_summary, [os.path.join(output_dir, 'correlation_heatmap.png')])

    create_markdown_story(llm_response, output_dir)
    
    print(f"Analysis complete!")

if __name__ == "__main__":
    main()
