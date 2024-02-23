from flask import Flask, render_template, request
import panel as pn
from bokeh.embed import server_document
from dotenv import load_dotenv
import os
import openai  # Fügen Sie diesen Import hinzu

# Importieren Sie cbfs aus utils.py, wenn es dort definiert ist
from utils import cbfs

# Stellen Sie sicher, dass alle benötigten Funktionen korrekt aus tool.py importiert werden
from tool import (
    get_crypto_data,
    get_reddit_data, 
    get_coingecko_market_data,
    get_historical_crypto_price,
    get_lunarcrush_galaxy_score,
    get_lunarcrush_alt_rank,
    # Fügen Sie hier die korrekte Import-Anweisung für get_bitquery_data hinzu, falls benötigt
)

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')  # Stellen Sie sicher, dass diese Zeile nach dem Import von openai steht

app = Flask(__name__)

# Initialisiere das conversational bot framework mit den Tools
# Stellen Sie sicher, dass die Variable `tools` korrekt definiert und initialisiert wird, bevor Sie sie verwenden
tools = [get_crypto_data, get_reddit_data, get_coingecko_market_data, get_historical_crypto_price, get_lunarcrush_galaxy_score, get_lunarcrush_alt_rank]
cb = cbfs(tools)

# Erstelle UI-Komponenten für die Webanwendung
# Da Sie die Funktionen zum Löschen des Chatverlaufs entfernen möchten, lassen wir diese Teile weg
inp = pn.widgets.TextInput(placeholder='Enter your query about the crypto market here…')

# Binde die Konversation an das Eingabefeld
conversation = pn.bind(cb.convchain, inp) 

# Erstelle das Dashboard-Layout
tab1 = pn.Column(
    pn.Row(inp, sizing_mode='stretch_width'),  # Zentrieren des Eingabefelds
    pn.layout.Divider(),
    pn.panel(conversation, loading_indicator=True, height=400),
)

dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# Lenox: Your Crypto Assistant'), sizing_mode='stretch_width'),
    pn.Tabs(('Conversation', tab1))
)

# Starte den Panel-Server
panel_server = pn.serve(dashboard, show=False, port=5000)

@app.route('/')
def index():
    # Integriere Bokeh für interaktive Visualisierungen
    bokeh_script = server_document(url=f'http://localhost:{panel_server.port}', relative_urls=True)
    return render_template('index.html', bokeh_script=bokeh_script)

if __name__ == '__main__':
    app.run(debug=True, port=5000)