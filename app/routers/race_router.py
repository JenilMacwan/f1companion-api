"""
Race router.

Endpoints: /next_race, /race_results/{round}/{year}
"""

from fastapi import APIRouter, HTTPException
import requests

from app.services.race_service import (
    get_next_race, 
    get_race_results,
    get_qualifying_results,
    get_sprint_results,
    get_sprint_qualifying_results
)

router = APIRouter()


@router.get("/next_race")
def next_race():
    try:
        return get_next_race()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/race_results/{round}/{year}")
def race_results(round: str, year: str):
    try:
        return get_race_results(round, year)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching F1 races: {str(e)}"
        )


@router.get("/qualifying_results/{round}/{year}")
def qualifying_results(round: str, year: str):
    try:
        return get_qualifying_results(round, year)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching qualifying results: {str(e)}"
        )


@router.get("/sprint_results/{round}/{year}")
def sprint_results(round: str, year: str):
    try:
        return get_sprint_results(round, year)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sprint results: {str(e)}"
        )


@router.get("/sprint_qualifying_results/{round}/{year}")
def sprint_qualifying_results(round: str, year: str):
    try:
        return get_sprint_qualifying_results(round, year)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sprint qualifying results: {str(e)}"
        )