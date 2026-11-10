# Application Montréal

L’outil `mtl_show_dashboard` ouvre un tableau de bord dans les clients compatibles avec [MCP Apps](https://modelcontextprotocol.io/extensions/apps). Il affiche la météo, les stations BIXI, les parcs et les arrêts STM autour d’un lieu montréalais.

Exemple : `mtl_show_dashboard(address="Hôtel de Ville de Montréal", radius_m=800, view="move")`.

Les vues `all`, `daily`, `move` et `out` sélectionnent les cartes initiales. Le tableau de bord ajoute les demandes 311 des 30 derniers jours, les panneaux d'interdiction de stationnement, les lots saisonniers de déneigement, les entraves et les lieux touristiques de Données Québec. Les demandes 311 publiées ne confirment pas une intervention. Les panneaux et les conditions sur place déterminent les règles de stationnement.

Pour l’ouvrir dans un navigateur, lancez `uv run python main.py` puis accédez à [localhost:8000/montreal](http://localhost:8000/montreal). Cliquez sur Explorer. Le serveur utilise le même outil que l’application intégrée.

La recherche accepte un rayon de 100 à 3000 mètres. Chaque source dispose de 25 secondes après le géocodage. Une erreur apparaît dans la section concernée; les autres résultats restent affichés. Les liens de source accompagnent les données. Les arrêts STM proviennent du catalogue GTFS et ne donnent pas les prochains départs. Les données météo sont attribuées à Open-Meteo (CC BY 4.0).

L'interface est en français, s'adapte aux petits écrans et fonctionne au clavier. La carte intégrée charge OpenStreetMap; chaque lieu dispose de liens OpenStreetMap et Google Maps. Les droits de la carte sont attribués aux contributeurs OpenStreetMap. Dans un client MCP Apps, les appels passent par le client hôte et les liens utilisent `ui/open-link`. La ressource `ui://mtl-mcp/montreal.html` est incluse dans le paquet Python; ses métadonnées autorisent uniquement `https://www.openstreetmap.org` comme domaine de carte intégrée. Les clients sans prise en charge des cadres intégrés peuvent utiliser le lien externe.

[English documentation](montreal-app.en.md)

## Couverture et dates

Le tableau de bord compose quinze sections à partir des outils MCP : météo, 311, stationnement, lots de déneigement, travaux, BIXI, STM, REM, avis municipaux, écocentres, murales, parcs, restaurants, tourisme et événements des sept prochains jours.

Pour le 311, il sélectionne les trente jours se terminant à la dernière date géolocalisée publiée dans la source consultée. Les archives portent les dates de début et de fin; elles ne décrivent pas la situation actuelle. L'outil `mtl_311_nearby` conserve la recherche sur la période actuelle par défaut; `use_latest_available=true` active cette période publiée.

Si le flux CIFS est indisponible, les travaux proviennent du jeu [Entraves et travaux en cours](https://www.donneesquebec.ca/recherche/dataset/vmtl-info-travaux). Les permis couvrant la date du jour ne confirment pas une fermeture à toute heure. La carte affiche le changement de source.

En l'absence de lot de déneigement dans le rayon demandé, la recherche passe à cinq kilomètres et affiche cet élargissement. La saison du fichier publié accompagne les résultats; les lots ne constituent pas une disponibilité en temps réel. Les écocentres sont les plus proches et peuvent aussi dépasser le rayon demandé. Le filtre géographique des événements est approximatif.

## Vérifier et connecter l'application

Démarrez le serveur avec `uv run python main.py`, puis exécutez `uv run python scripts/smoke_mcp_app.py --url http://127.0.0.1:8000/mcp`. Le script vérifie la découverte de l'outil, la ressource HTML `ui://`, le résultat structuré, les quinze sections et le lien OpenStreetMap. Il signale séparément les sources indisponibles.

Pour tester le pont dans un navigateur, lancez `uv run python -m http.server 8014 --bind 127.0.0.1`, puis ouvrez `http://127.0.0.1:8014/tests/fixtures/mcp_app_host.html`. La fixture simule l'hôte et vérifie les messages, les filtres et les thèmes. Elle ne constitue pas un test dans ChatGPT.

Pour le rendu natif dans ChatGPT, [le guide OpenAI](https://developers.openai.com/plugins/build/app-quickstart) demande un endpoint MCP accessible publiquement en HTTPS, puis la connexion de l'app dans ChatGPT. Une URL `ui://` désigne la ressource à l'intérieur de la connexion MCP; elle ne connecte pas automatiquement le serveur local au compte ChatGPT. Après connexion, demandez à ChatGPT d'appeler `mtl_show_dashboard`.

Le navigateur utilise `POST /montreal/api`, qui valide les mêmes arguments que l'outil MCP. Le thème clair ou sombre provient du contexte de l'hôte; les cartes longues défilent dans leur cadre.
