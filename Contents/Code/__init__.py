KEY = "4703ed5e1e3df52b10dd"
SEARCH_QUERY_URL = "http://hummingbird.me/api/v1/search/anime"
SEARCH_ID_URL = "http://hummingbird.me/api/v1/anime/"
SEARCH_DETAIL_ID_URL = "https://hummingbird.me/api/v2/anime/"


def do_search(results, media, lang, mediatype):
    Log("[HUMMINGBIRD_SEARCH][NOTICE]: Starting search")
    Log("[HUMMINGBIRD_SEARCH][Notice]: Inizializing variables for " + media.show)
    # Init variables
    if mediatype == "tvshow":
        show_name = media.show
    elif mediatype == "movie":
        show_name = media.name
    anime_id = None
    anime_title = None
    anime_year = None
    anime_match_score = None

    # Request URL
    data_url = SEARCH_QUERY_URL + "?query=" + String.Quote(show_name, usePlus=True)
    Log("[HUMMINGBIRD_SEARCH][Notice]: Requesting data from: " + data_url)

    # Request Data
    try:
        data = JSON.ObjectFromURL(data_url)
        Log("[HUMMINGBIRD_SEARCH][Notice]: Data retrived")
    except:
        Log("[HUMMINGBIRD_SEARCH][Error]: Error retriving data from " + data_url)
        Log("[HUMMINGBIRD_SEARCH][ERROR]: Search interrupted")
        return

    # Elaborate Data
    Log("[HUMMINGBIRD_SEARCH][Notice]: Elaborating data")
    for anime in data:
        anime_id = str(anime["id"])
        anime_title = str(anime["title"])
        anime_year = int(str(anime["started_airing"]).split("-")[0])
        anime_match_score = int(100 - abs(String.LevenshteinDistance(anime_title, show_name)))

        if anime["alternate_title"] is not None:
            Log("[HUMMINGBIRD_SEARCH][Notice]: Anime present alternate title, checking match")
            alternate_title = str(anime["alternate_title"])
            alternate_match_score = int(100 - abs(String.LevenshteinDistance(alternate_title, show_name)))
            if alternate_match_score > anime_match_score:
                Log("[HUMMINGBIRD_SEARCH][Notice]: Using alternate title")
                anime_title = alternate_title
                anime_match_score = alternate_match_score

        Log("[HUMMINGBIRD_SEARCH][Notice]: Add anime entry to results")
        results.Append(MetadataSearchResult(id=anime_id, name=anime_title, year=anime_year, score=anime_match_score,
                                            lang=Locale.Language.English))

    Log("[HUMMINGBIRD_SEARCH][NOTICE]: Search completed")
    return


def do_update_tvshow(metadata, media, lang):
    Log("[HUMMINGBIRD_UPDATE][NOTICE]: Starting update")

    data_url = SEARCH_DETAIL_ID_URL + metadata.id
    Log("[HUMMINGBIRD_UPDATE][Notice]: Requesting data")
    try:
        anime = JSON.ObjectFromURL(data_url, None, {"X-Client-Id": "4703ed5e1e3df52b10dd"})["anime"]
    except:
        Log("[HUMMINGBIRD_UPDATE][Error]: Failed to retrive data from " + data_url)
        Log("[HUMMINGBIRD_UPDATE][ERROR]: Update interrupted")
        return
    Log("[HUMMINGBIRD_UPDATE][Notice]: Data retrived")
    Log("[HUMMINGBIRD_UPDATE][Notice]: Updating metadata")
    metadata.title = str(anime["titles"]["canonical"])
    metadata.summary = str(anime["synopsis"])
    metadata.rating = float(anime["community_rating"] / 5) * 10
    metadata.originally_available_at = Datetime.ParseDate(anime["started_airing_date"])
    metadata.content_rating = str(anime["age_rating"])
    metadata.posters[str(anime["poster_image"])] = Proxy.Media(HTTP.Request(str(anime["poster_image"])).content)
    metadata.duration = int(anime["episode_length"])
    metadata.genres = anime["genres"]

    metadata.studio = str(anime["producers"][0])
    metadata.art[str(anime["cover_image"])] = Proxy.Media(HTTP.Request(str(anime["cover_image"])).content)
    for season in metadata.seasons:
        season.posters = metadata.posters
    Log("[HUMMINGBIRD_UPDATE][Notice]: Metadata updated")

    Log("[HUMMINGBIRD_UPDATE][NOTICE]: Update Completed")
    return


class HummingbirdAgentTV(Agent.TV_Shows):
    name = "Hummingbird.me"
    languages = [Locale.Language.English]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.opensubtitles']

    def search(self, results, media, lang):
        do_search(results, media, lang, "tvshow")
        return

    def update(self, metadata, media, lang):
        do_update_tvshow(metadata, media, lang)
        return