from typing import Any, Dict
from fastapi import Request


async def get_db(request: Request):
    # Lazy import to avoid bringing heavy DB deps at module import time
    from database import DatabaseManager
    from config import Config

    db = getattr(request.app.state, 'db', None)
    if db is None:
        # lazy-init for non-production usage
        config = Config()
        db = DatabaseManager(config)
        await db.connect()
        request.app.state.db = db
    return db


def get_anonymizer(request: Request):
    from anonymizer import DataAnonymizer
    from config import Config

    anon = getattr(request.app.state, 'anonymizer', None)
    if anon is None:
        config = Config()
        anon = DataAnonymizer(config)
        request.app.state.anonymizer = anon
    return anon


def get_response_builder(request: Request):
    from response_builder import ResponseBuilder

    rb = getattr(request.app.state, 'response_builder', None)
    if rb is None:
        rb = ResponseBuilder()
        request.app.state.response_builder = rb
    return rb


async def get_orders_service(arguments: Dict[str, Any], db, anonymizer, response_builder):
    # call DB, anonymize and build response
    result = await db.get_orders(**arguments)
    anonymized = anonymizer.anonymize_orders(result)
    response = response_builder.build_orders_response(anonymized, arguments)
    return response
