from .store import make_store
from logging import getLogger
import requests
log = getLogger(__name__)


def create_get_place(settings):
    cache = make_store(settings['cache'])
    key_format = '{}:{}'
    base_url = "https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&sensor=false&result_type={type}&key={key}"

    def get_place(lat, lon):
        key = key_format.format(lat, lon)
        cache_result = cache.load(key)
        if cache_result is not None:
            return cache_result

        response = requests.get(base_url.format(
            lat=lat,
            lon=lon,
            type='administrative_area_level_1|administrative_area_level_2|administrative_area_level_3|point_of_interest|natural_feature|locality',
            key=settings['google-api-key']
        ))
        if response.ok:
            place = response.json()['results'][0]['formatted_address']
            log.info('Got place for {}, {}: {}'.format(lat, lon, place))
        else:
            place = False
        cache.save(key, place)
        return place

    return get_place
