import asyncio
import logging
import os
from typing import List
from urllib.parse import quote_plus

import aiohttp
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfReadError

load_dotenv()


async def fetch_results(session: aiohttp.ClientSession, prompt: str, n: int) -> List[str]:
    params = {"q": prompt, "num": n, "hl": "en", "api_key": os.getenv("SERPAPI_KEY"), "engine": "google", "filter": "1", "as_filetype": "pdf"}

    url = f"https://serpapi.com/search.json?{quote_plus('&'.join(f'{k}={v}' for k, v in params.items()))}"

    try:
        async with session.get(url) as response:
            if response.status == 200:
                results = await response.json()
                if "organic_results" in results:
                    return [result["link"] for result in results["organic_results"] if result["link"].lower().endswith(".pdf")]
    except Exception as e:
        logging.error(f"Error searching for '{prompt}': {str(e)}")
    return []


async def get_links(session: aiohttp.ClientSession, condition: str, n: int = 5) -> List[str]:
    prompts = [
        f"{condition} causes",
        f"{condition} risk factors",
        f"{condition} symptoms",
        f"{condition} prevention and cure",
        f"{condition} diagnosis",
        f"{condition} treatment options",
        f"{condition} prognosis",
        f"{condition} complications",
        f"{condition} epidemiology",
        f"{condition} research and studies",
        f"{condition} latest treatments and advancements",
    ]

    tasks = [fetch_results(session, prompt, n) for prompt in prompts]

    results = await asyncio.gather(*tasks)

    all_links = list(set([link for prompt_results in results for link in prompt_results]))

    return all_links


async def download_pdf(session: aiohttp.ClientSession, url: str, filename: str) -> bool:
    """
    Download a single PDF file asynchronously
    """
    try:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                with open(filename, "wb") as f:
                    while True:
                        chunk = await response.content.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                return True
            return False
    except Exception as e:
        logging.error(f"Error downloading {url}: {str(e)}")
        return False


async def download_all_pdfs(session: aiohttp.ClientSession, links: List[str], email: str) -> int:
    """
    Download all PDFs asynchronously, store them in the path pdfs/{email}/file
    """
    # Create the directory for the email
    path = os.path.join("pdfs", email)
    if not os.path.exists(path):
        os.makedirs(path)

    tasks = []
    for idx, url in enumerate(links, 1):
        filename = os.path.join(path, f"file{idx}.pdf")
        task = asyncio.create_task(download_pdf(session, url, filename))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    for idx, result in enumerate(results, 1):
        filename = os.path.join(path, f"file{idx}.pdf")
        if result:
            if not validate_pdf(filename):
                os.remove(filename)
                logging.info(f"Removed invalid PDF: {filename}")

    return len([result for result in results if result])  # Return count of successfully downloaded PDFs


def validate_pdf(file_path: str) -> bool:
    """
    Validate if a file is a valid PDF
    """
    try:
        PdfReader(file_path)
        return True
    except PdfReadError:
        logging.error(f"{file_path} - Invalid PDF file")
        return False
    except Exception as e:
        logging.error(f"Error validating {file_path}: {str(e)}")
        return False


async def scrape(condition: str, email: str):
    """
    Main function to scrape PDF links and download them.
    """
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/118.0", "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.5"}) as session:
        pdf_links = await get_links(session, condition, n=10)
        print(f"Found {len(pdf_links)} unique PDF links")

        downloaded = await download_all_pdfs(session, pdf_links, email)
        print(f"Successfully downloaded {downloaded} PDFs")
