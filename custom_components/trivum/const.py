"""Konstanten für die trivum-Integration."""

DOMAIN = "trivum"

CONF_HOST = "host"
CONF_PORT = "port"
DEFAULT_PORT = 80
SCAN_INTERVAL_SECONDS = 5

# Zonenbefehle (siehe trivum-API, Abschnitt 1.1)
CMD_POWER_OFF = 1
CMD_VOLUME_INC = 3
CMD_VOLUME_DEC = 4
CMD_POWER_ON = 7
CMD_DEFAULT_LINEIN = 48
CMD_DEFAULT_STREAMING = 50
CMD_DEFAULT_TUNER = 51
CMD_NEXT = 400
CMD_PREV = 401
CMD_PLAY = 431
CMD_PAUSE = 432
CMD_STOP = 433
CMD_MUTE_ON = 680
CMD_MUTE_OFF = 681

# Pfade für Quellenlisten
LIST_PATHS = {
    "Favorit": ("/api/v1/trivum/favorite.xml", "f"),
    "Playlist": ("/api/v1/trivum/playlist.xml", "y"),
    "TuneIn": ("/api/v1/tunein/favorite.xml", "i"),
}
