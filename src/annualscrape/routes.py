# src/annualscrape/routes.py

from fastapi import APIRouter, BackgroundTasks, status
from .handler import ScraperHandler

router = APIRouter()
handler = ScraperHandler()

@router.post("/scrape", tags=["Scraping"], status_code=status.HTTP_202_ACCEPTED)
async def trigger_full_scrape(background_tasks: BackgroundTasks):
    """
    Triggers the scraping process for ALL companies as a background task.
    """
    background_tasks.add_task(handler.run_full_scrape)
    return {"message": "Full scraping process started in the background. Check server logs for progress."}

# <<< NEW SECTION: Individual endpoints for each company >>>

@router.post("/scrape/wika", tags=["Scraping"], status_code=status.HTTP_202_ACCEPTED)
async def trigger_wika_scrape(background_tasks: BackgroundTasks):
    """
    Triggers the scraping process for WIKA only.
    """
    background_tasks.add_task(handler.run_single_scrape, "wika")
    return {"message": "Scraping process for WIKA started in the background."}


@router.post("/scrape/waskita", tags=["Scraping"], status_code=status.HTTP_202_ACCEPTED)
async def trigger_waskita_scrape(background_tasks: BackgroundTasks):
    """
    Triggers the scraping process for WASKITA only.
    """
    background_tasks.add_task(handler.run_single_scrape, "waskita")
    return {"message": "Scraping process for WASKITA started in the background."}


@router.post("/scrape/hutama", tags=["Scraping"], status_code=status.HTTP_202_ACCEPTED)
async def trigger_hutama_scrape(background_tasks: BackgroundTasks):
    """
    Triggers the scraping process for HUTAMA KARYA only.
    """
    background_tasks.add_task(handler.run_single_scrape, "hutama")
    return {"message": "Scraping process for HUTAMA KARYA started in the background."}


@router.post("/scrape/ptpp", tags=["Scraping"], status_code=status.HTTP_202_ACCEPTED)
async def trigger_ptpp_scrape(background_tasks: BackgroundTasks):
    """
    Triggers the scraping process for PTPP only.
    """
    background_tasks.add_task(handler.run_single_scrape, "ptpp")
    return {"message": "Scraping process for PTPP started in the background."}

