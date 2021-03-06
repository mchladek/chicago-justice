from __future__ import unicode_literals
from functools import lru_cache
import logging
from math import isnan
from django.core.exceptions import ObjectDoesNotExist
import tagnews
import numpy as np

from newsarticles.models import TrainedCategoryRelevance, TrainedCoding, TrainedLocation, Category

MIN_CATEGORY_RELEVANCE = 0.05
MIN_LOCATION_RELEVANCE = 0.5

LOG = logging.getLogger(__name__)

# Memoize taggers, they are slow to instantiate
@lru_cache(maxsize=1)
def crime_tagger():
    return tagnews.CrimeTags()

@lru_cache(maxsize=1)
def geo_tagger():
    return tagnews.GeoCoder()

@lru_cache(maxsize=1)
def sent_evaller():
    return tagnews.SentimentGoogler()

def current_model_info():
    return 'tagnews {}'.format(tagnews.__version__)

def tag_article(article):
    try:
        locations = extract_locations(article)
        category_scores, max_score = tag_categories(article)
    except Exception as e:
        LOG.exception(e)
        return

    TrainedCoding.objects.filter(article=article).delete()

    coding = TrainedCoding.objects.create(
        article=article,
        model_info=current_model_info(),
        relevance=max_score,
        bin=None
    )

    for (category, relevance) in category_scores:
        if (relevance > MIN_CATEGORY_RELEVANCE):
            TrainedCategoryRelevance.objects.create(
                coding=coding,
                category=category,
                relevance=relevance
            )

    for location in locations:
        TrainedLocation.objects.create(coding=coding, **location)

def tag_categories(article):
    if len(article.bodytext) < 10:
        return [], 0

    probs = crime_tagger().tagtext_proba(article.bodytext)

    category_scores = []
    max_score = 0

    for abbr, score in zip(probs.index, probs.values):
        try:
            category = Category.objects.get(abbreviation=abbr)
            category_scores.append((category, score))
            max_score = max(score, max_score)
        except ObjectDoesNotExist:
            LOG.warn('category not found: %s', abbr)

    return category_scores, max_score

def extract_locations(article):
    if len(article.bodytext) < 10:
        return []

    tokenized_locations, tokenized_scores = geo_tagger().extract_geostrings(
        article.bodytext,
        prob_thresh=MIN_LOCATION_RELEVANCE
    )
    best_location = []
    if tokenized_locations:
        best_location = geo_tagger().best_geostring((tokenized_locations, tokenized_scores))
    location_strings = [' '.join(gl) for gl in tokenized_locations]

    (coords, scores) = geo_tagger().lat_longs_from_geostring_lists(tokenized_locations)
    com_areas = geo_tagger().community_area_from_coords(coords)
    lats = coords['lat'].tolist()
    lngs = coords['long'].tolist()

    combined = zip(location_strings, lats, lngs, scores, com_areas)
    trained_locations = []
    for location, lat, lng, confidence, neighborhood in combined:
        if not isnan(lat) and not isnan(lng) and not isnan(confidence):
            trained_locations.append({
                'text': location,
                'latitude': lat,
                'longitude': lng,
                'confidence': confidence,
                'neighborhood': neighborhood,
                'is_best': location == ' '.join(best_location)
            })
    return trained_locations

def bin_article_for_sentiment(article, cpd_user_val, cpd_model_val):
    if len(article.bodytext) < 10:
        return -1

    bin = sent_evaller().extract_google_priority_bin(article.bodytext, cpd_user_val, cpd_model_val)
    return bin

def calculate_units(article):
    return np.ceil(len(article)/1000)

def get_api_reponse(article):
    sentiment_json = sent_evaller().call_api(article)
    return sentiment_json

def extract_sentiment_information(sentiment_json):
    """
    :param sentiment_json: json response from api
    :return: ix: list index of this police entity
             entity: words of the entity phrase
             sent_val: sent score
    """
    for ix, entity in enumerate(sentiment_json.entities):
        police_entity = sent_evaller().is_police_entity(entity)
        if police_entity:
            sent_val = sent_evaller().sentiment_from_entity(police_entity)
            assert bool((ix, entity, sent_val)) # bool of the yielded value is always True
            yield (ix, entity, sent_val)
    return False
