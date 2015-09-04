from googleplaces import GooglePlaces, types
from .store import make_store
from logging import getLogger
log = getLogger(__name__)


def create_get_place(settings):
    google_places = GooglePlaces(settings['google api key'])
    cache = make_store(settings['cache'])
    key_format = '{}:{}'

    def get_place(lat, lon):
        key = key_format.format(lat, lon)
        cache_result = cache.load(key)
        if cache_result:
            return cache_result

        query_result = google_places.nearby_search(lat_lng={
            'lat': lat,
            'lng': lon
        }, types=[types.TYPE_LOCALITY])

        for place in query_result.places:
            place.get_details()
            cache.save(key, place)
            log.info('Got place for {}, {}'.format(lat, lon))
            return place

    return get_place
