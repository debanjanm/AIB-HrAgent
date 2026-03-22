# AIB-HrAgent

A Flask-based web application that parses LinkedIn job descriptions and outputs structured JSON documents.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AIB-HrAgent.git
   cd AIB-HrAgent
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python app.py
```

The app will start a local server at `http://127.0.0.1:5000/`.

### API Endpoint

**POST /parse_jd**

Parses a LinkedIn job description and returns structured JSON.

#### Request
- Method: POST
- Content-Type: application/json
- Body:
  ```json
  {
    "jd": "Job Title: Software Engineer\nCompany: ABC Corp\nLocation: Remote\n..."
  }
  ```

#### Response
- Status: 200 OK
- Content-Type: application/json
- Body:
  ```json
  {
    "job_title": "Software Engineer",
    "company": "ABC Corp",
    "location": "Remote",
    "employment_type": "",
    "salary": "",
    "job_description": "...",
    "requirements": [],
    "benefits": ""
  }
  ```

### Example

Using curl:
```bash
curl -X POST http://127.0.0.1:5000/parse_jd \
  -H "Content-Type: application/json" \
  -d '{"jd": "Job Title: Data Scientist\nCompany: XYZ Ltd\nLocation: New York"}'
```

## Troubleshooting

- Ensure the virtual environment is activated before running the app.
- If Flask is not found, reinstall dependencies: `pip install -r requirements.txt`.
- The app runs in debug mode by default; for production, set `debug=False` in `app.py`.