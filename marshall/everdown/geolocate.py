from googleplaces import GooglePlaces, types


def create_get_city(google_api_key):
    google_places = GooglePlaces(google_api_key)

    def get_city(lat, lon):
        query_result = google_places.nearby_search(lat_lng={
            'lat': lat,
            'lng': lon
        }, types=[types.TYPE_LOCALITY])

        for result in query_result.places:
            return result.vicinity

    return get_city