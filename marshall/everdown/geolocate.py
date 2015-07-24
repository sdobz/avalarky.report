from googleplaces import GooglePlaces, types


def create_get_place(google_api_key):
    google_places = GooglePlaces(google_api_key)

    def get_place(lat, lon):
        query_result = google_places.nearby_search(lat_lng={
            'lat': lat,
            'lng': lon
        }, types=[types.TYPE_LOCALITY])

        for place in query_result.places:
            place.get_details()
            return place

    return get_place
