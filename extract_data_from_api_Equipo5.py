import requests
import pandas as pd


def get_season(now):
    if isinstance(now, datetime):
        now = now.date()
    now = now.replace(year=2000)
    return next(season for season, (start, end) in seasons
                if start <= now <= end)


api_key = ''  # Add your API key here.

headers = {
    'User-Agent': ''
}

url = 'https://api.rawg.io/api/games?key=' + api_key + '&dates=2020-01-01,2020-10-31&page_size=40'

r = requests.get(url=url, headers=headers)

current_page = r.json()

columns = ['name', 'slug', 'released', 'genre', 'rating', 'metacritic']

games_list = []

platform_count = {}

game_count = 0
total_games = current_page.get('count')

print(current_page.get('next'))

while current_page is not None:

    json = current_page

    if json.get('results') is not None:
        for game in json.get('results'):
            name = game.get('name')
            slug = game.get('slug')
            released = game.get('released')
            genre = "none"
            rating = game.get('rating')
            metacritic = game.get('metacritic')

            if game.get('genres'):
                genre = game.get('genres')[0].get('name')

            if game.get('platforms') is not None:
                for platform in game.get('platforms'):

                    current_platform = platform.get('platform').get('name')

                    if current_platform in platform_count:

                        platform_count[current_platform] = platform_count[current_platform] + 1

                    else:

                        platform_count[current_platform] = 1

            current_game = {'name': name, 'slug': slug, 'released': released, 'genre': genre, 'rating': rating, 'metacritic': metacritic}

            games_list.append(current_game)

            game_count = game_count + 1

            print(name)

    print("\nGame Count: " + str(game_count) + " from " + str(total_games))

    if current_page.get('next') is not None:
        current_page = requests.get(url=current_page.get('next'), headers=headers).json()

    else:
        current_page = None


games_data_frame = pd.DataFrame(games_list, columns=columns)

platform_data_frame = pd.DataFrame(platform_count.items(), columns=['platform', 'count'])

games_data_frame.to_csv('AllReleasedGamesData_2017_2020.csv', index=False)
platform_data_frame.to_csv('PlatformCountGamesData_2017_2020.csv', index=False)
