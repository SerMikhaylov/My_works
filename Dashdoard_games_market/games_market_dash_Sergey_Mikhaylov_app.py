import dash
import codecs
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import pandas as pd
pd.options.plotting.backend = "plotly"
import json

import plotly.express as px

card_height_s = '18rem'
card_height = '34rem'

file = 'games.csv'

# Load spreadsheet
df = pd.read_csv(file, delimiter=',')

#исключаем проекты ранее 2000 года
df = df.loc[df.Year_of_Release >= 2000]

#исключаем проекты, для которых имеются пропуски данных в любой из колонок
df = df.dropna()
df = df.sort_values("Year_of_Release")

#создаем уникальные значения различных параметров для фильтров
choose_genre = sorted(df["Genre"].unique())
choose_rating = sorted(df["Rating"].unique())
choose_year_of_Release = sorted(df["Year_of_Release"].unique())

# убираем все нечисловые данные из колонки User_Score
df = df.drop(df[df.User_Score == 'tbd'].index)
# преобразуем данные колонки User_Score в числовые значения
df['User_Score'] = pd.to_numeric(df['User_Score'])
# сортируем DataFrame по возрастанию оценок пользователей (User_Score) для построения кросс-плота
df = df.sort_values(by=['User_Score'])

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

f = codecs.open("setup.json", "r", "utf-8")
setup_file = json.load(f)

#Фильтр 1 - Фильтр жанров
filter_genre = dbc.FormGroup(
    [
        dbc.Label("Выбор жанра игры", html_for="genre_game"),
        dcc.Dropdown(
            id="genre_game",
            placeholder='Жанр',
            value=None,
            options=[{'label': genre, 'value': genre} for genre in choose_genre],
            multi = True # множественный выбор
        ),
    ],
)
#Фильтр 2 - Фильтр рейтингов
filter_rating = dbc.FormGroup(
    [
        dbc.Label("Выбор рейтинга игры", html_for="rating"),
        dcc.Dropdown(
            id="rating",
            placeholder='Рейтинг',
            value=None,
            options=[{'label': rating, 'value': rating} for rating in choose_rating],
            multi = True # множественный выбор
        ),
    ],
)

#Фильтр 3 - Интервал годов выпуска игр
filter_date_start = dbc.FormGroup([
    dbc.Label("Интервал выпуска игр:  ", html_for="filter-date_start"),
    dcc.Dropdown(
            id="start_date",
            placeholder='Дата начала',
            value=None,
            options=[{'label': start_date, 'value': start_date} for start_date in choose_year_of_Release],
            multi = False # множественный выбор
        ),
    ],
)

filter_date_end = dbc.FormGroup([
    # dbc.Label("", html_for="filter-date_end"),
    dcc.Dropdown(
            id="finish_date",
            placeholder='Дата окончания',
            value=None,
            options=[{'label': finish_date, 'value': finish_date} for finish_date in choose_year_of_Release],
            multi = False # множественный выбор
        ),
    ],
)

# Вспомогательные функции
def filter_time(genre, rating, start_date, finish_date, df):
    df_filter = df.copy()
    if genre is not None:
        df_filter = df_filter[df_filter["Genre"].isin(genre)]
    if rating is not None:
        df_filter = df_filter[df_filter["Rating"].isin(rating)]
    if start_date is not None:
        df_filter = df_filter[df_filter["Year_of_Release"] >= start_date]
    if finish_date is not None:
        df_filter = df_filter[df_filter["Year_of_Release"] <= finish_date]
    return df_filter

# надпись по умолчанию в Text area
text_ar_val = "Количество выбранных игр:"

#расположение полей
app.layout = html.Div(children=[
    dbc.Row([
        dbc.Col(html.Label(
            setup_file['themeSettings'][0]['title'],
            style={
                "text-align": "left",
                "font-size": 25,
            }
        ))], style={'margin-bottom': '5px'}),
        html.Br(),
    dbc.Row([
        dbc.Col(html.Label(
            setup_file['themeSettings'][0]['description'],
            style={
                "text-align": "left",
                'font-size': 15,
                "color": "#000000"
            }
        ))],
        style={'margin-bottom': '15px'}),
    dbc.Row([
        dbc.Col([filter_genre], width={'size':6}),
        dbc.Col([filter_rating], width={'size':6})],
        style={'margin-bottom': '15px'}),
    # ),
    dbc.Row([
        dbc.Col(
            dcc.Textarea(
                id='num_game_filter',
                className='num_game_filter',
                # value = f"Количество выбранных игр: {len(df['Name'].unique())}",
                value = text_ar_val,
                style={'width': '50%', 'height': 30},)
        )],
        style={'margin-bottom': '15px'}),
    dbc.Row([
        # dbc.Col(dcc.Graph(id='game-production-stacked-area-plot', figure=fig2), width={'size':6}),
        # dbc.Col(dcc.Graph(id='games-score-scatter-plot', figure=fig), width={'size':6})],
        dbc.Col(dcc.Graph(id='game-production-stacked-area-plot'), width={'size':6}),
        dbc.Col(dcc.Graph(id='games-score-scatter-plot'), width={'size':6})],
        style={'margin-bottom': '15px'}),
    dbc.Row([
        dbc.Col([filter_date_start], width = {'size':3})],
        style={'margin-bottom': '3px'}),
    dbc.Row([
        dbc.Col([filter_date_end], width = {'size':3})])
])

# CALLBACKS

@app.callback(
    Output(component_id='games-score-scatter-plot', component_property='figure'),
    [
        Input(component_id='genre_game', component_property='value'),
        Input(component_id='rating', component_property='value'),
        Input(component_id='start_date', component_property='value'),
        Input(component_id='finish_date', component_property='value'),
    ]
)
def update_scatter_plot(genre, rating, start_date, finish_date):
    df_filter = filter_time(genre, rating, start_date, finish_date, df)
    fig = px.scatter(df_filter, x='User_Score', y='Critic_Score', color="Genre")
    return fig

@app.callback(
    Output(component_id='game-production-stacked-area-plot', component_property='figure'),
    [
        Input(component_id='genre_game', component_property='value'),
        Input(component_id='rating', component_property='value'),
        Input(component_id='start_date', component_property='value'),
        Input(component_id='finish_date', component_property='value'),
    ]
)
def update_stacked_area_plot(genre, rating, start_date, finish_date):
    df_filter = filter_time(genre, rating, start_date, finish_date, df)
    fig = df_filter.groupby(['Year_of_Release','Platform']).size().unstack().plot.area()
    return fig

@app.callback(
    Output(component_id='num_game_filter', component_property='value'),
    [
        Input(component_id='genre_game', component_property='value'),
        Input(component_id='rating', component_property='value'),
        Input(component_id='start_date', component_property='value'),
        Input(component_id='finish_date', component_property='value'),
    ]
)
def update_text_area(genre, rating, start_date, finish_date):
    df_filter = filter_time(genre, rating, start_date, finish_date, df)
    value = f"Количество выбранных игр: {len(df_filter['Name'].unique())}"
    return value

if __name__ == "__main__":
    app.run_server(debug=True)