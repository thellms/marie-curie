# Project README

## Project Overview

This directory is part of a research project for Lucia Cobos, focusing on the relationship between carnivores and Neanderthals. The goal of this project is to develop an AI agent that can automatically find and download academic papers related to specific queries, and then build a GraphRAG (Graph-based Retrieval-Augmented Generation) with the collected data.

## Directory Structure

```
/Users/asdls/Documents/python/icarehb/src/dbs/
├── README.md
├── scripts/
├── data/
└── models/
```

- `scripts/`: Contains the scripts for querying databases, downloading papers, and processing data.
- `data/`: Stores the downloaded papers and any intermediate data files.
- `models/`: Includes the models and configurations for building the GraphRAG.

## Getting Started

1. **Clone the Repository**: 
    ```bash
    git clone <repository_url>
    ```

2. **Install Dependencies**: 
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Query Script**: 
    ```bash
    python scripts/query_papers.py --query "carnivores and Neanderthals"
    ```

## Usage

- **Querying Papers**: Use the `query_papers.py` script to search for and download relevant papers.
- **Building GraphRAG**: Use the `build_graphrag.py` script to process the downloaded papers and construct the GraphRAG.

## TODO List

- Create an agent to refine user queries at the beginning of the experience. The agent should ensure it has a great query for creating sub-queries and then evaluate the relevance of the papers (based on the abstracts).
- Create an agent that iterates with sub-queries by searching in the API and analyzing the number of results (too many, too few, etc.).

## Contributing

If you would like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact

For any questions or inquiries, please contact Adrián Sánchez de la Sierra at [adrian.s.delasierral@gmail.com].
