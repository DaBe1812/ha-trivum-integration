<p align="center">
  <img src="custom_components/trivum/brand/logo.png" alt="trivum" width="320">
</p>

# trivum für Home Assistant

Inoffizielle Integration für trivum-Multiroom-Audiosysteme über die lokale HTTP/XML-Schnittstelle.
Jede Zone erscheint als `media_player` (Ein/Aus, Lautstärke, Mute, Transport, Quellenauswahl mit
Favoriten, Playlists und TuneIn).

> Nicht von trivum technologies GmbH entwickelt oder unterstützt. „trivum“ ist eine Marke der jeweiligen Inhaber.

## Installation über HACS

1. HACS → ⋮ → *Benutzerdefinierte Repositories* → URL dieses Repos, Kategorie *Integration*
2. „trivum“ installieren, Home Assistant neu starten
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → *trivum* → IP/Hostname eingeben

## Hinweise

- Abfrage per Polling alle 5 Sekunden, keine Authentifizierung (wie die trivum-API selbst)
- Der Mute-Status wird von der API nicht geliefert und daher nur angenommen
