import requests
import pandas as pd
import holidays
from datetime import date, datetime

# From user jfs in Stack Overflow:
Y = 2000  # dummy leap year to allow input X-02-29 (leap day)
seasons = [('winter', (date(Y, 1, 1), date(Y, 3, 20))),
           ('spring', (date(Y, 3, 21), date(Y, 6, 20))),
           ('summer', (date(Y, 6, 21), date(Y, 9, 22))),
           ('autumn', (date(Y, 9, 23), date(Y, 12, 20))),
           ('winter', (date(Y, 12, 21), date(Y, 12, 31)))]


def get_season(now):
    if isinstance(now, datetime):
        now = now.date()
    now = now.replace(year=Y)
    return next(season for season, (start, end) in seasons
                if start <= now <= end)


api_key = ''

headers = {
    'User-Agent': ''
}

url = 'https://api.rawg.io/api/games?key=' + api_key + '&dates=2020-01-01,2020-11-28&page_size=40'

r = requests.get(url=url, headers=headers)

current_page = r.json()

# print(current_page)

columns_facts = ['GameKey', 'DateKey', 'DeveloperKey', 'PublisherKey', 'PlatfromKey', 'StoreKey', 'ESRBKey', 'PublicRating',
                 'Metacritic', 'Playtime', 'OwnerReviews']
game_release_facts = []

columns_date = ['DateKey', 'FullDate', 'DayNumber', 'MonthNumber', 'Year', 'CalendarQuarter', 'Season',
                'HolidayIndicator']
date_dimension = []
date_dimension_keys = {}

columns_game = ['GameKey', 'GameName', 'MainGenre', 'SubGenre']
game_dimension = []
game_dimension_keys = {}

columns_developer = ['DeveloperKey', 'DeveloperName', 'NumberGamesDeveloped', 'AsOfFullDate']
developer_dimension = []
developer_dimension_keys = {}

columns_publisher = ['PublisherKey', 'PublisherName', 'NumberGamesPublished', 'AsOfFullDate']
publisher_dimension = []
publisher_dimension_keys = {}

columns_esrb = ['ESRBKey', 'Rating Name']
esrb_dimension = []
esrb_dimension_keys = {}

columns_platform = ['PlatformKey', 'PlatformName']
platform_dimension = []
platform_dimension_keys = {}

columns_store = ['StoreKey', 'StoreName', 'URL']
store_dimension = []
store_dimension_keys = {}

game_count = 0
total_games = current_page.get('count')

print(current_page.get('next'))
number_of_facts = 500

keep = True

while game_count < number_of_facts:

    # print("si entra nueva p")

    json = current_page

    if json.get('results') is not None:
        for game in json.get('results'):
            name = game.get('name')
            slug = game.get('slug')
            released = game.get('released')
            genre = "none"
            sub_genre = "none"
            rating = game.get('rating')
            metacritic = game.get('metacritic')
            playtime = game.get('playtime')
            owner_reviews = game.get('ratings_count')

            if game.get('genres'):
                genre = game.get('genres')[0].get('name')

                if len(game.get('genres')) > 1:
                    sub_genre = game.get('genres')[1].get('name')

            # Dimension FKs:
            game_key = None
            date_key = None
            developer_key = None
            publisher_key = None
            esrb_key = None

            # Get Dimensions:
            # Game Dimension:
            if slug in game_dimension_keys:
                game_key = slug

            else:
                new_game_dimension = {'GameKey': slug, 'GameName': name, 'MainGenre': genre, 'SubGenre': sub_genre}
                game_dimension.append(new_game_dimension)
                game_dimension_keys[slug] = slug
                game_key = slug

            # Date Dimension:
            if released in date_dimension_keys:
                date_key = released

            else:
                current_datetime = datetime.strptime(released, '%Y-%m-%d')
                day_number = int(current_datetime.strftime("%d"))
                month_number = int(current_datetime.strftime("%m"))
                year = current_datetime.strftime("%Y")
                quarter = (int(month_number) // 4) + 1

                date_season = get_season(current_datetime)

                holiday = False

                us_holidays = holidays.UnitedStates()
                mx_holidays = holidays.CountryHoliday('MX')

                if released in us_holidays:
                    holiday = True

                if released in mx_holidays:
                    holiday = True

                new_date_dimension = {'DateKey': released, 'FullDate': released, 'DayNumber': day_number,
                                      'MonthNumber': month_number, 'Year': year, 'CalendarQuarter': quarter,
                                      'Season': date_season, 'HolidayIndicator': holiday}
                date_dimension.append(new_date_dimension)
                date_dimension_keys[released] = released
                date_key = released

            # Get game's developer, publisher, and esrb data:
            url_details = 'https://api.rawg.io/api/games/' + slug + '?key=' + api_key

            r_details = requests.get(url=url_details, headers=headers)

            details = r_details.json()

            consultation_date = date.today().strftime('%Y-%m-%d')

            if details.get('developers') is not None and len(details.get('developers')) > 0:
                developer_slug = details.get('developers')[0].get('slug')
                developer_name = details.get('developers')[0].get('name')
                developer_game_count = details.get('developers')[0].get('games_count')

                if developer_slug in developer_dimension_keys:
                    developer_key = developer_slug

                else:
                    new_developer = {'DeveloperKey': developer_slug, 'DeveloperName': developer_name,
                                     'NumberGamesDeveloped': developer_game_count, 'AsOfFullDate': consultation_date}
                    developer_dimension.append(new_developer)
                    developer_dimension_keys[developer_slug] = developer_slug
                    developer_key = developer_slug

            if details.get('publishers') is not None and len(details.get('publishers')) > 0:
                publisher_slug = details.get('publishers')[0].get('slug')
                publisher_name = details.get('publishers')[0].get('name')
                publisher_game_count = details.get('publishers')[0].get('games_count')

                if publisher_slug in publisher_dimension_keys:
                    publisher_key = publisher_slug

                else:
                    new_publisher = {'PublisherKey': publisher_slug, 'PublisherName': publisher_name,
                                     'NumberGamesPublished': publisher_game_count, 'AsOfFullDate': consultation_date}
                    publisher_dimension.append(new_publisher)
                    publisher_dimension_keys[publisher_slug] = publisher_slug
                    publisher_key = publisher_slug

            else:
                publisher_slug = 'independent'

                if publisher_slug in publisher_dimension_keys:
                    publisher_key = publisher_slug

                else:
                    new_publisher = {'PublisherKey': publisher_slug, 'PublisherName': "Self Published",
                                     'NumberGamesPublished': None, 'AsOfFullDate': consultation_date}
                    publisher_dimension.append(new_publisher)
                    publisher_dimension_keys[publisher_slug] = publisher_slug
                    publisher_key = publisher_slug

            if details.get('esrb_rating') is not None:
                esrb_slug = details.get('esrb_rating').get('slug')
                esrb_name = details.get('esrb_rating').get('name')

                if esrb_slug in esrb_dimension_keys:
                    esrb_key = esrb_slug

                else:
                    new_esrb = {'ESRBKey': esrb_slug, 'Rating Name': esrb_name}
                    esrb_dimension.append(new_esrb)
                    esrb_dimension_keys[esrb_slug] = esrb_slug
                    esrb_key = esrb_slug

            else:
                esrb_slug = 'not-yet-rated'

                if esrb_slug in esrb_dimension_keys:
                    esrb_key = esrb_slug

                else:
                    new_esrb = {'ESRBKey': esrb_slug, 'Rating Name': "Not yet rated"}
                    esrb_dimension.append(new_esrb)
                    esrb_dimension_keys[esrb_slug] = esrb_slug
                    esrb_key = esrb_slug

            if game.get('platforms') is not None:
                for platform in game.get('platforms'):

                    platform_key = None

                    current_platform_slug = platform.get('platform').get('slug')

                    if current_platform_slug in platform_dimension_keys:
                        platform_key = current_platform_slug

                    else:
                        platform_name = platform.get('platform').get('name')
                        new_plaform = {'PlatformKey': current_platform_slug, 'PlatformName': platform_name}
                        platform_dimension.append(new_plaform)
                        platform_dimension_keys[current_platform_slug] = current_platform_slug
                        platform_key = current_platform_slug

                    if current_platform_slug == 'pc' or current_platform_slug == 'linux':

                        store_key = None

                        if details.get('stores') is not None:
                            for store in details.get('stores'):
                                current_store_slug = store.get('store').get('slug')

                                if current_store_slug != "playstation-store" and current_store_slug != "nintendo" and current_store_slug != 'apple-appstore':

                                    if current_store_slug in store_dimension_keys:
                                        store_key = current_store_slug

                                    else:
                                        current_store_domain = store.get('store').get('domain')
                                        current_store_name = store.get('store').get('name')

                                        new_store = {'StoreKey': current_store_slug, 'StoreName': current_store_name, 'URL': current_store_domain}
                                        store_dimension.append(new_store)
                                        store_dimension_keys[current_store_slug] = current_store_slug
                                        store_key = current_store_slug

                                    # Add release fact:
                                    current_game_release_facts = {'GameKey': game_key, 'DateKey': date_key, 'DeveloperKey': developer_key, 'PublisherKey': publisher_key, 'PlatfromKey': platform_key, 'StoreKey': store_key, 'ESRBKey': esrb_key, 'PublicRating': rating, 'Metacritic': metacritic, 'Playtime': playtime, 'OwnerReviews': owner_reviews}
                                    game_release_facts.append(current_game_release_facts)

                    else:

                        store_key = None

                        if details.get('stores') is not None and len(details.get('stores')) > 0:
                            current_store_slug = None
                            current_store_name = None
                            current_store_domain = None

                            if platform_key == 'playstation5' or platform_key == 'playstation4' or platform_key == 'playstation3':
                                current_store_slug = 'playstation-store'
                                current_store_name = 'PlayStation Store'
                                current_store_domain = 'store.playstation.com'

                            if platform_key == 'xbox-one' or platform_key == 'xbox-360' or platform_key == 'xbox-series-x' or platform_key == 'xbox-series-s':
                                current_store_slug = 'xbox-store'
                                current_store_name = 'Xbox Store'
                                current_store_domain = 'microsoft.com'

                            if platform_key == 'nintendo-3ds' or platform_key == 'nintendo-switch':
                                current_store_slug = 'nintendo'
                                current_store_name = 'Nintendo Store'
                                current_store_domain = 'nintendo.com'

                            if platform_key == 'macos' or platform_key == 'ios':
                                current_store_slug = 'apple-appstore'
                                current_store_name = 'App Store'
                                current_store_domain = 'apps.apple.com'

                            if platform_key == 'android':
                                current_store_slug = 'google-play'
                                current_store_name = 'Google Play'
                                current_store_domain = 'play.google.com'

                            if current_store_slug in store_dimension_keys:
                                store_key = current_store_slug

                            else:
                                new_store = {'StoreKey': current_store_slug, 'StoreName': current_store_name,
                                             'URL': current_store_domain}
                                store_dimension.append(new_store)
                                store_dimension_keys[current_store_slug] = current_store_slug
                                store_key = current_store_slug

                        # Add release fact:
                        current_game_release_facts = {'GameKey': game_key, 'DateKey': date_key,
                                                      'DeveloperKey': developer_key, 'PublisherKey': publisher_key,
                                                      'PlatfromKey': platform_key, 'StoreKey': store_key,
                                                      'ESRBKey': esrb_key, 'PublicRating': rating,
                                                      'Metacritic': metacritic, 'Playtime': playtime,
                                                      'OwnerReviews': owner_reviews}

                        game_release_facts.append(current_game_release_facts)

            game_count = game_count + 1

            print(name)

    print("\nGame Count: " + str(game_count) + " from " + str(number_of_facts))

    if current_page.get('next') is not None:
        current_page = requests.get(url=current_page.get('next'), headers=headers).json()

    else:
        current_page = None


game_release_facts_data_frame = pd.DataFrame(game_release_facts, columns=columns_facts)

date_dimension_data_frame = pd.DataFrame(date_dimension, columns=columns_date)

game_dimension_data_frame = pd.DataFrame(game_dimension, columns=columns_game)

developer_dimension_data_frame = pd.DataFrame(developer_dimension, columns=columns_developer)

publisher_dimension_data_frame = pd.DataFrame(publisher_dimension, columns=columns_publisher)

store_dimension_data_frame = pd.DataFrame(store_dimension, columns=columns_store)

esrb_dimension_data_frame = pd.DataFrame(esrb_dimension, columns=columns_esrb)

platform_dimension_data_frame = pd.DataFrame(platform_dimension, columns=columns_platform)

print(game_release_facts_data_frame.head())
print(date_dimension_data_frame.head())
print(game_dimension_data_frame.head())
print(developer_dimension_data_frame.head())
print(publisher_dimension_data_frame.head())
print(store_dimension_data_frame.head())
print(esrb_dimension_data_frame.head())
print(platform_dimension_data_frame.head())

game_release_facts_data_frame.to_csv('game_release_facts2018.csv', index=False)
date_dimension_data_frame.to_csv('date_dimension2018.csv', index=False)
game_dimension_data_frame.to_csv('game_dimension2018.csv', index=False)
developer_dimension_data_frame.to_csv('developer_dimension2018.csv', index=False)
publisher_dimension_data_frame.to_csv('publisher_dimension2018.csv', index=False)
store_dimension_data_frame.to_csv('store_dimension2018.csv', index=False)
esrb_dimension_data_frame.to_csv('esrb_rating_dimension2018.csv', index=False)
platform_dimension_data_frame.to_csv('platform_dimension2018.csv', index=False)

# games_data_frame.to_csv('AllReleasedGamesData_2017_2020.csv', index=False)
# platform_data_frame.to_csv('PlatformCountGamesData_2017_2020.csv', index=False)
