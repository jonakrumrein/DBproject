import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import plotly.express as px

from collections import Counter

import base64

from mysqldb import Mysql
from influx import Influx
from addPlayer import addPlayer
from config import token, org, url, bucket, dbPlayersLayout


app = dash.Dash(__name__, title='Faceit Stats')

db = Mysql(host="localhost", user="root", password="root", database="faceit")
influx = Influx(token=token, org=org, bucket=bucket, url=url)

result = db.checkIfTableExists('players')
if not result:
    db.addTable(dbPlayersLayout)

players = db.select('players', None, 'name')

app.layout = html.Div([

    html.H3("Faceit Stat Checker"),
    dbc.Row([
        dbc.Col([
            dcc.Input(id='input', type='text', placeholder='Enter the player to add...'),
            dbc.Button(id='submit-button-state', n_clicks=0, children='Add Player'),
        ]),
    ]),

    dbc.Row([

        dbc.Col([
            dcc.Dropdown(
                id='player1',
                options=[{'label': i['name'], 'value': i['name']} for i in players],
                placeholder='Select player one...'
            ),
        ], md=4), 

        dbc.Col([
            dcc.Dropdown(
                id='yaxis',
                options=[{'label': 'Kills', 'value': 'kills'},
                {'label': 'Deaths', 'value': 'deaths'},
                {'label': 'Assists', 'value': 'assists'},
                {'label': 'Headshot Rate', 'value': 'headshots'},
                {'label': 'Triple Kills', 'value': 'triples'},
                {'label': 'Quad Kills', 'value': 'quads'},
                {'label': 'Aces', 'value': 'pentas'},
                {'label': 'K/D', 'value': 'kpd'},
                {'label': 'KPR', 'value': 'kpr'},
                {'label': 'Win', 'value': 'win'}],
                placeholder='Select the stat to compare...'
            ),
        ], md=4),

        dbc.Col([
            dcc.Dropdown(
                id='player2',
                options=[{'label': i['name'], 'value': i['name']} for i in players],
                placeholder='Select player two...'
            ),
        ], md=4),

    ], no_gutters=True, style={"margin-bottom": "20px"}),

    dbc.Row([
        dbc.Col([
            dbc.CardGroup([
                dbc.Card([
                    dbc.CardImg(id='player1-img'),
                    dbc.CardBody([
                        html.H4(id='player1-name'),
                        dbc.Table(html.Tbody([html.Tr([
                            html.Td(html.Img(id='player1-level', style={'width': '50px', 'height': '50px'})),
                            html.Td(id='player1-elo')
                        ])])),
                        dbc.Button("Go to Steam Profile", id='player1-steam')
                    ])
                ], color="dark", inverse=True),

                dbc.Card([
                    dbc.CardBody([
                        html.H1("VS", style={"text-align": "center", "font-size": "80px"}),
                    ])
                ], color="dark", inverse=True),

                dbc.Card([
                    dbc.CardImg(id='player2-img'),
                    dbc.CardBody([
                        html.H4(id='player2-name'),
                        dbc.Table(html.Tbody([html.Tr([
                            html.Td(html.Img(id='player2-level', style={'width': '50px', 'height': '50px'})),
                            html.Td(id='player2-elo')
                        ])])),
                        dbc.Button("Go to Steam Profile", id='player2-steam')
                    ])
                ], color="dark", inverse=True)
            ]),
        ], width={"size": 6, "offset": 3})
    ]),

    dbc.Row([

        dbc.Col([
            dcc.Graph(id='pie-chart-1'),
        ], 
        id='pie-chart-div1',
        width=6,
        style={'display': 'none'}),

        dbc.Col([
            dcc.Graph(id='pie-chart-2'),
        ], 
        id='pie-chart-div2',
        width=6,
        style={'display': 'none'})
    ], no_gutters=True,),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='indicator-graphic')),
    ]),
])


@app.callback(
    Output('player1', 'options'),
    Output('player2', 'options'),
    Input('submit-button-state', 'n_clicks'),
    State('input', 'value'),
)
def update_output_div(nClicks, input):
    if input:
        addPlayer(db, input)
    
    players = [{"label": i['name'], "value": i['name']} for i in db.select('players', None, 'name')]
    return players, players


@app.callback(
    Output('player1-name', 'children'),
    Output('player1-img', 'src'),
    Output('player1-steam', 'href'),
    Output('player1-elo', 'children'),
    Output('player1-level', 'src'),
    Input('player1', 'value'),
)
def update_output_div(input):
    if input:
        player = db.select('players', "name = '{}'".format(input), 'name', 'avatar', 'steamProfile', 'faceitElo', 'skillLevel')
        img_filename = "data/level_" + player[0]['skillLevel'] + ".png"
        encoded_img = base64.b64encode(open(img_filename, 'rb').read())
        return player[0]['name'], player[0]['avatar'], "https://steamcommunity.com/profiles/{}".format(player[0]['steamProfile']), player[0]['faceitElo'], 'data:image/png;base64,{}'.format(encoded_img.decode())
    else:
        return '', '', '', '', ''

@app.callback(
    Output('player2-name', 'children'),
    Output('player2-img', 'src'),
    Output('player2-steam', 'href'),
    Output('player2-elo', 'children'),
    Output('player2-level', 'src'),
    Input('player2', 'value'),
)
def update_output_div(input):
    if input:
        player = db.select('players', "name = '{}'".format(input), 'name', 'avatar', 'steamProfile', 'faceitElo', 'skillLevel')
        img_filename = "data/level_" + player[0]['skillLevel'] + ".png"
        encoded_img = base64.b64encode(open(img_filename, 'rb').read())
        return player[0]['name'], player[0]['avatar'], "https://steamcommunity.com/profiles/{}".format(player[0]['steamProfile']), player[0]['faceitElo'], 'data:image/png;base64,{}'.format(encoded_img.decode())
    else:
        return '', '', '', '', ''


@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('player1', 'value'),
    Input('player2', 'value'),
    Input('yaxis', 'value'),
)
def update_graph(player1, player2, yaxis):
    
    if player1 and yaxis:
        player1Id = db.select('players', "name = '{}'".format(player1), 'playerId')[0]['playerId']
    else: 
        player1Id = ''
    if player2 and yaxis:
        player2Id = db.select('players', "name = '{}'".format(player2), 'playerId')[0]['playerId']
    else: 
        player2Id = ''

    if yaxis and player1 or yaxis and player2 :
        query = '''
            from(bucket: "{}")
                |> range(start: -30d)\
                |> filter(fn: (r) => r["_measurement"] == "stats")
                |> filter(fn: (r) => r["_field"] == "{}")
                |> filter(fn: (r) => r["host"] == "{}" or r["host"] == "{}")
                |> yield(name: "mean")
        '''.format(bucket, yaxis, player1Id, player2Id)

        df = influx.query(query, True)

        fig = px.line(df, x='_time', y='_value', color='host', title='',
                labels=dict(_time="time", _value=yaxis, host='player')        
        )
        fig.data[0].update(mode='markers+lines')
        if len(fig.data) > 1:
            fig.data[1].update(mode='markers+lines')
    
        return fig
    else:
        return px.line(title='Choose one or more players to show their stats!')
    

@app.callback(
    Output('pie-chart-1', 'figure'),
    Output('pie-chart-div1', 'style'),
    Output('pie-chart-2', 'figure'),
    Output('pie-chart-div2', 'style'),
    Input('player1', 'value'),
    Input('player2', 'value'),
)
def update_piechart(player1, player2):

    if player1 and not player2:
        return createPieChart(player1), {'display': 'inline'}, px.pie(), {'display': 'none'}
    if player2 and not player1:
        return px.pie(), {'display': 'none'}, createPieChart(player2), {'display': 'inline'}
    if player1 and player2:
        return createPieChart(player1), {'display': 'inline'}, createPieChart(player2), {'display': 'inline'}
    else:
        return px.pie(), {'display': 'none'}, px.pie(), {'display': 'none'}


def createPieChart(player):

    playerId = db.select('players', "name = '{}'".format(player), 'playerId')[0]['playerId']

    query = '''
            from(bucket: "{}")
                |> range(start: -30d)\
                |> filter(fn: (r) => r["_measurement"] == "stats")
                |> filter(fn: (r) => r["_field"] == "map")
                |> filter(fn: (r) => r["host"] == "{}")
                |> yield(name: "mean")
        '''.format(bucket, playerId)

    result = influx.query(query)
    results = []
    for table in result:
        for record in table.records:
            results.append((record.get_value()))

    df = pd.DataFrame(Counter(results).items())

    return px.pie(df, values=1, names=0, title="Maps played: " + player)


if __name__ == '__main__':
    app.run_server(debug=True)