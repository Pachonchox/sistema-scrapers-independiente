
# GEMINI.md

## Project Overview

This project is a sophisticated web scraping system (version 5) designed to extract product information from various Chilean retailers. It is built with Python and utilizes a modern stack including Playwright for browser automation, PostgreSQL for data storage, and potentially FastAPI for serving an API. The system is designed to be robust, with features like intelligent retries, error handling, and detailed logging.

The project is structured around a core "portable orchestrator" (`portable_orchestrator_v5`) that can be run as a standalone module. This orchestrator manages the scraping process, including initializing scrapers for different retailers, running them in cycles, and handling the data they collect.

A key feature of the project is the "Master System," which is responsible for data normalization, generating unique product codes, and detecting arbitrage opportunities. This suggests that the project is not just about scraping data, but also about processing and analyzing it to provide valuable insights.

The project also includes a command-line interface (CLI) for running the scrapers, tests, and maintenance tasks. This makes it easy to interact with the system and customize its behavior.

## Building and Running

### Prerequisites

*   Python 3.9+
*   PostgreSQL
*   Redis

### Installation

1.  **Clone the repository.**
2.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers:**

    ```bash
    playwright install chromium
    ```

4.  **Set up the environment:**

    Create a `.env` file in the root of the project and add the following variables:

    ```env
    # PostgreSQL
    DATA_BACKEND=postgres
    PGHOST=localhost
    PGPORT=5432
    PGDATABASE=orchestrator
    PGUSER=postgres
    PGPASSWORD=postgres

    # Master System
    MASTER_SYSTEM_ENABLED=true
    NORMALIZATION_ENABLED=true
    COMPARISON_ENABLED=true
    ARBITRAGE_ENABLED=true

    # Configuración de scraping
    MAX_CONCURRENT_PAGES=3
    PAGE_TIMEOUT=60000
    SCROLL_WAIT=3000
    ```

5.  **Start the services:**

    ```bash
    docker-compose up -d
    ```

### Running the Scrapers

The main entry point for running the scrapers is `run_orchestrator_v5.py`. This script provides a flexible command-line interface for controlling the scraping process.

**Run the orchestrator with default settings:**

```bash
python run_orchestrator_v5.py
```

**Run a quick test:**

```bash
python run_orchestrator_v5.py --test
```

**Run only the Paris and Ripley scrapers:**

```bash
python run_orchestrator_v5.py --scrapers paris ripley
```

**Run the standalone orchestrator:**

The `portable_orchestrator_v5` module can be run as a standalone scraper.

```bash
python portable_orchestrator_v5/main.py --retailer ripley --category celulares --max-products 20 --export-excel
```

## Development Conventions

*   **Code Style:** The code follows the PEP 8 style guide.
*   **Logging:** The project uses the `logging` module for detailed logging. The logs include timestamps, log levels, and emojis to make them easy to read.
*   **Error Handling:** The code includes robust error handling and a retry mechanism to make the scraping process more reliable.
*   **Modularity:** The project is well-structured and modular, with different components responsible for different tasks. This makes it easy to understand, maintain, and extend the codebase.
*   **Configuration:** The project uses a combination of a `.env` file and command-line arguments for configuration. This provides a flexible way to configure the system for different environments and use cases.
