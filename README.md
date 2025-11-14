# Indeed & Glassdoor Scraper

Indeed Glassdoor Scraper is a Python-based web scraping project designed to extract job postings and detailed information from **Indeed** and **Glassdoor**. It collects key fields such as job title, company name, location, salary (if available), job description, and links. Output can be saved in CSV or JSON format, and results can be displayed via HTML.

---

## 🚀 Features

* Scrape job listings from **Indeed** and **Glassdoor**
* Extract essential fields:

  * Job Title
  * Company Name
  * Location
  * Salary (if available)
  * Job Description
  * Job URL
* Save results to **CSV** or **JSON**
* Modular codebase for easy expansion

---

## 🛠️ Technologies Used

* **Python**

  * requests
  * BeautifulSoup (bs4)
  * pandas (optional)
* **HTML/CSS** (for results display)

---

## 📥 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/daltonium/indeed-glassdoor-scraper.git
cd indeed-glassdoor-scraper
```

### 2. Install Dependencies

Using `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests beautifulsoup4 pandas
```

---

## ▶️ Usage

### Scraping Indeed

1. Open `indeed_scraper.py` and set your target URL and search parameters.
2. Run the script:

```bash
python indeed_scraper.py
```

Output will display in the terminal or save to file depending on script customization.

### Scraping Glassdoor

1. Open `glassdoor_scraper.py`.
2. Run:

```bash
python glassdoor_scraper.py
```

### Result Visualization

* Open the HTML file inside `templates/` to view scraped results in your browser.
* Or load generated CSV/JSON into your preferred analysis tool.

---

## 📂 File Structure

```
├── indeed_scraper.py      # Script for scraping Indeed
├── glassdoor_scraper.py   # Script for scraping Glassdoor
├── templates/             # HTML templates
├── static/                # CSS/JS assets
├── data/                  # Output datasets (CSV/JSON)
├── requirements.txt       # Python dependencies
```

---

## 🔧 How It Works

* Make GET requests to job listing pages using custom request headers.
* Parse returned HTML with **BeautifulSoup**.
* Extract job listing fields (title, company, location, salary, etc.).
* Save data into CSV or JSON.

---

## 📈 Tips & Scaling

* Use random delays and rotate user agents for large-scale scraping.
* Consider proxy services or scraping APIs (Scrapingdog, ScrapingBee) to avoid blocks.
* Always respect website **robots.txt** and **terms of service**.

---

## 🤝 Contributing

1. Fork the repository
2. Create a new branch
3. Submit a pull request with clear details

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 📬 Contact

Open an issue on GitHub for bug reports or feature requests.

---

## ✔️ Quick Review

* Scrapes job listings from Indeed & Glassdoor using Python + BeautifulSoup
* Saves structured data for analysis
* Modular and easy to extend
* Add screenshots or sample outputs to further enhance the README
