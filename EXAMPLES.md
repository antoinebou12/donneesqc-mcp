# Exemples de requêtes — Données Québec MCP

Tous les exemples ci-dessous ont été testés avec le serveur MCP (appels live juillet 2026). Les réponses sont générées automatiquement par l'agent IA à partir des données ouvertes en temps réel. Les tableaux sont des instantanés : les totaux évoluent avec les portails sources.

Présentation : **verdict court** → **tableau markdown** → **URL source**. Pas d'histogramme ASCII ; ignorer les objets JSON `chart` en chat.

[Retour au README](README.md)

---

## Système (`common_*`)

### 1. Version du serveur MCP

**Requête :**
> « Quelle version du serveur MCP tourne, et quelles capacités sont activées ? »

**Outils utilisés :** `common_get_version`

**Réponse (juillet 2026) :**

Serveur **donneesqc-mcp**, version de développement active (ex. `0.0.0-dev` selon le build). Capacités : Données Québec, Montréal, IGO, géocodage, La bicyclette, Collecte MTL, murales, avis/alertes.

| Capacité | Activée |
|---|---|
| Données Québec (CKAN) | oui |
| donnees.montreal.ca | oui |
| IGO WMS/WFS | oui |
| Adresses Québec | oui |
| La bicyclette / Collecte / Murales / Avis | oui |

**Source :** serveur local / déployé (`common_get_version`)

---

### 2. Catalogue d'outils avec exemples

**Requête :**
> « Liste les outils géospatiaux (`qc/geo`) avec un exemple d'appel. »

**Outils utilisés :** `common_list_tools_with_examples`

**Réponse :**

`common_list_tools_with_examples(category="qc/geo")` → **8** outils dans la catégorie `qc/geo` (couches, features, WMS, géocodage, conversion, intersection).

Astuce : sans `category`, l'outil regroupe tous les préfixes (`qc`, `mtl`, `common`, …).

**Source :** introspection MCP

---

## Données Québec (catalogue et accès)

### 3. Statistiques globales du catalogue

**Requête :**
> « Combien d'organisations publient des données sur Données Québec ? Quels sont les thèmes dominants ? »

**Outils utilisés :** `qc_get_catalog_stats`

**Réponse (juillet 2026) :**

**142 organisations**, **1615 jeux de données**.

| Organisation | Jeux de données |
|---|---|
| Ville de Montréal | 389 |
| Ville de Laval | 130 |
| Ministère de l’Environnement, de la Lutte contre les changements climatiques, de la Faune et des Parcs | 128 |
| Ministère des Ressources naturelles et des Forêts | 121 |
| Ville de Gatineau | 52 |
| Ville de Repentigny | 39 |
| Ville de Trois-Rivières | 38 |
| Ville de Québec | 37 |
| Ministère de la Santé et des services sociaux | 34 |
| Ministère des Transports et de la Mobilité durable | 31 |

Thèmes (groupes CKAN) — catalogue complet :

| Thème | Jeux |
|---|---|
| Environnement, ressources naturelles et énergie | 476 |
| Infrastructures | 379 |
| Gouvernement et finances | 273 |
| Transport | 210 |
| Loi, justice et sécurité publique | 167 |

**Source :** [Données Québec](https://www.donneesquebec.ca/)

---

### 4. Thèmes de la Ville de Montréal

**Requête :**
> « Répartition des jeux de la Ville de Montréal par thème (Gouvernement et finances, Infrastructures, Environnement…) ? »

**Outils utilisés :** `qc_get_catalog_stats`

**Réponse (juillet 2026) :**

`qc_get_catalog_stats(organization="ville-de-montreal")` → **389** jeux, thèmes :

| Thème | Jeux |
|---|---|
| Gouvernement et finances | 115 |
| Infrastructures | 94 |
| Environnement, ressources naturelles et énergie | 88 |
| Transport | 35 |
| Société et culture | 29 |
| Loi, justice et sécurité publique | 23 |
| Tourisme, sports et loisirs | 20 |
| Politiques sociales | 16 |
| Économie et entreprises | 8 |
| Santé | 6 |
| Agriculture et alimentation | 6 |
| Éducation et recherche | 4 |

**Source :** [Données Québec — Ville de Montréal](https://www.donneesquebec.ca/recherche/organization/ville-de-montreal)

---

### 5. Organisations du catalogue

**Requête :**
> « Liste les organisations dont le nom contient « ville », puis donne le détail de la Ville de Montréal. »

**Outils utilisés :** `qc_list_organizations` > `qc_get_organization_info`

**Réponse :**

`qc_list_organizations(query="ville")` retourne **22** organisations (Montréal 389 jeux, Laval 130, Gatineau 52, etc.).

`qc_get_organization_info(org_id="ville-de-montreal")` : politique d'ouverture par défaut, **389** jeux publiés sur Données Québec.

**Source :** [Données Québec](https://www.donneesquebec.ca/)

---

### 6. Jeux de données de la Ville de Laval

**Requête :**
> « Quels jeux de données la Ville de Laval publie sur Données Québec ? Montre-moi les plus récents avec leurs ressources. »

**Outils utilisés :** `qc_search_datasets` (filtré par organisation) > `qc_list_dataset_resources`

**Réponse :**

La Ville de Laval publie **130 jeux de données**. Filtrez avec `organization="ville-de-laval"` et une requête textuelle (ex. `query="laval"`).

**Source :** [Données Québec — Ville de Laval](https://www.donneesquebec.ca/recherche/organization/ville-de-laval)

---

### 7. Accès rapide en un appel — actes criminels

**Requête :**
> « Trouve les actes criminels à Montréal et montre-moi quelques lignes. »

**Outils utilisés :** `qc_find_and_query`

**Réponse :**

En un seul appel (`query="actes criminels montreal"`), l'outil enchaîne recherche, ressource DataStore et aperçu :

- Dataset : **Actes criminels** (Ville de Montréal) — [vmtl-actes-criminels](https://www.donneesquebec.ca/recherche/dataset/vmtl-actes-criminels)
- Colonnes : `CATEGORIE`, `DATE`, `QUART`, `PDQ`, `LONGITUDE`, `LATITUDE`
- Centaines de milliers d'enregistrements au DataStore

**Source :** [Données Québec](https://www.donneesquebec.ca/recherche/dataset/vmtl-actes-criminels)

---

### 8. Métadonnées et ressource — événements publics

**Requête :**
> « Donne-moi les métadonnées du jeu Événements publics, puis le détail de la ressource CSV. »

**Outils utilisés :** `qc_get_dataset_info` > `qc_get_resource_info`

**Réponse (juillet 2026) :**

`qc_get_dataset_info(dataset_id="vmtl-evenements-publics")` :

| Champ | Valeur |
|---|---|
| Titre | Événements publics |
| Licence | Attribution (CC-BY 4.0) |
| Ressources | 3 |
| Slug | vmtl-evenements-publics |

Ressources typiques : CSV (DataStore), SHP, GeoJSON.
`qc_get_resource_info(resource_id="6decf611-6f11-4f34-bb36-324d804c9bad")` → `datastore_active: true`, format CSV.

**Source :** [Événements publics](https://www.donneesquebec.ca/recherche/dataset/vmtl-evenements-publics)

---

### 9. Détection de ressource et aperçu

**Requête :**
> « Trouve le meilleur fichier pour le jeu Actes criminels sur Données Québec, puis montre le schéma. »

**Outils utilisés :** `qc_auto_detect_resource` > `qc_preview_resource`

**Réponse :**

1. `qc_auto_detect_resource(dataset_name="vmtl-actes-criminels")` → ressource CSV DataStore recommandée.
2. `qc_preview_resource` → schéma + 5 premières lignes + `total_rows`.

**Source :** [Données Québec](https://www.donneesquebec.ca/recherche/dataset/vmtl-actes-criminels)

---

### 10. Interrogation DataStore — événements à venir

**Requête :**
> « Montre quelques événements publics Montréal triés par date de début (les plus lointains). »

**Outils utilisés :** `qc_query_resource_data`

**Réponse (juillet 2026) :**

`qc_query_resource_data(resource_id="6decf611-6f11-4f34-bb36-324d804c9bad", sort="date_debut desc", page_size=5, fields="titre,type_evenement,date_debut,arrondissement")` — **5 859** lignes au total.

| Titre | Type | Début | Arrondissement |
|---|---|---|---|
| Avant que la dernière feuille ne tombe - Collect… | Théâtre | 2027-05-16 | Verdun |
| Classiques de Mozart à Stravinsky - Orchestre mé… | Musique | 2027-05-13 | Verdun |
| Frédérique Cournoyer Lessard Scuse Théâtre et ar… | Art de la parole | 2027-05-13 | Outremont |
| Avant que la dernière feuille ne tombe - Collect… | Théâtre | 2027-05-13 | Rivière-des-Prairies–Pointe-aux-Trembles |
| Accepte-toi comme je suis - Emmanuelle Roberge | Cinéma | 2027-05-13 | LaSalle |

**Source :** [Événements publics](https://www.donneesquebec.ca/recherche/dataset/vmtl-evenements-publics)

---

### 11. Téléchargement hors DataStore — réseau cyclable GeoJSON

**Requête :**
> « Télécharge un aperçu GeoJSON du réseau cyclable Montréal (ressource non-DataStore). »

**Outils utilisés :** `qc_list_dataset_resources` > `qc_download_resource`

**Réponse :**

Sur [vmtl-pistes-cyclables](https://www.donneesquebec.ca/recherche/dataset/vmtl-pistes-cyclables), la ressource GeoJSON n'est pas dans le DataStore.
`qc_download_resource(..., max_rows=2)` retourne un échantillon de features (format GeoJSON).

| Jeu | Format | Échantillon |
|---|---|---|
| Réseau cyclable | GeoJSON | 2 features |

**Source :** [Réseau cyclable](https://www.donneesquebec.ca/recherche/dataset/vmtl-pistes-cyclables)

---

### 12. SQL guidé — types d'événements publics

**Requête :**
> « Propose du SQL sur les événements publics, puis compte par type d'événement. »

**Outils utilisés :** `qc_suggest_sql` > `qc_query_resource_sql`

**Réponse (juillet 2026) :**

| Type d'événement | Total |
|---|---|
| Sport et plein air | 1261 |
| Art et artisanat | 558 |
| Heure du conte | 532 |
| Conseil et comité | 499 |
| Jeux | 459 |
| Musique | 382 |
| Théâtre | 286 |
| Cinéma | 278 |

Exemple SQL :

```sql
SELECT "type_evenement", COUNT(*) AS total
FROM "6decf611-6f11-4f34-bb36-324d804c9bad"
GROUP BY "type_evenement"
ORDER BY total DESC
LIMIT 8
```

**Source :** [Événements publics](https://www.donneesquebec.ca/recherche/dataset/vmtl-evenements-publics)

---

### 13. Comparaison de deux jeux

**Requête :**
> « Compare les actes criminels et les interventions des pompiers de Montréal sur Données Québec. »

**Outils utilisés :** `qc_compare_datasets`

**Réponse :**

Identifiants : `vmtl-actes-criminels` vs `vmtl-interventions-service-securite-incendie-montreal`.

| | Actes criminels | Interventions pompiers |
|--|-----------------|------------------------|
| Organisation | Ville de Montréal | Ville de Montréal |
| Licence | CC-BY 4.0 | CC-BY 4.0 |
| Tags communs | Sécurité publique | Sécurité publique |

**Source :** [Données Québec](https://www.donneesquebec.ca/)

---

## Géospatial (`qc_geo_*`)

### 14. Couches patrimoniales du Québec

**Requête :**
> « Quelles couches géospatiales sont disponibles pour le patrimoine culturel du Québec ? »

**Outils utilisés :** `qc_geo_list_layers` > `qc_geo_describe_layer`

**Réponse :**

Filtre `query="MCC"` : **7 couches** du Ministère de la Culture et des Communications (sur ~29 couches WFS IGO), ex. `ms:MCC_V_SITE_PATRIMONIAL_NATIONAL_S`.

**Source :** [IGO / geoegl](https://geoegl.msp.gouv.qc.ca/ws/igo_gouvouvert.fcgi)

---

### 15. Entités WFS — casernes d'incendie

**Requête :**
> « Récupère quelques casernes d'incendie via WFS. »

**Outils utilisés :** `qc_geo_get_features`

**Réponse (juillet 2026) :**

`qc_geo_get_features(layer_name="ms:CASERNE", max_features=5)` → **5** features (GeoJSON). Coordonnées IGO souvent en EPSG:32198 dans les propriétés `coord_x` / `coord_y` (WGS84).

| N° | SSI | Adresse |
|---|---|---|
| 1 | SSI Dolbeau-Mistassini | 1150, boulevard Vézina, Dolbeau-Mistassini G8L3K9 |
| 4 | SSI Dolbeau-Mistassini | 312, rue Édouard-Niquet, Péribonka G0W2G0 |
| St-Louis-Blandford | RIM-Incentraide (R4125) | 80, rue Principale,  Saint-Louis-de-Blandford, Qc  |
| 54 | SSI Les Îles-de-la-Madeleine | 004 Errol Road Grosse-Ile  Îles-de-la-Madeleine Gr |
| 4 | RIM-Le GÉANT (R4903) | 193, rue Principale, Girardville G0W1R0 |

**Source :** [IGO WFS](https://geoegl.msp.gouv.qc.ca/ws/igo_gouvouvert.fcgi)

---

### 16. Carte WMS des casernes d'incendie

**Requête :**
> « Génère une carte WMS des casernes d'incendie dans la région de Montréal. »

**Outils utilisés :** `qc_geo_get_map_url`

**Réponse :**

URL GetMap générée avec le bbox de Montréal (`-73.7,45.4,-73.4,45.6`) et la couche casernes (PNG 800×600).

**Source :** [IGO WMS](https://geoegl.msp.gouv.qc.ca/ws/igo_gouvouvert.fcgi)

---

### 17. Géocodage et reverse

**Requête :**
> « Géocode 900 Boulevard René-Lévesque Est à Québec, puis retrouve l'adresse près de 45.5017, -73.5673. »

**Outils utilisés :** `qc_geo_geocode` > `qc_geo_reverse_geocode`

**Réponse (exemple) :**

1. `qc_geo_geocode` → candidats Adresses Québec.
2. `qc_geo_reverse_geocode` → adresse québécoise la plus proche (ICherche).

**Source :** [Adresses Québec / ICherche](https://geoegl.msp.gouv.qc.ca/apis/icherche)

---

### 18. Intersection spatiale et conversion de coordonnées

**Requête :**
> « Dans quel arrondissement de Montréal se trouve le point 45.5017, -73.5673 ? Convertis aussi ces coordonnées en Lambert MTQ. »

**Outils utilisés :** `qc_geo_spatial_intersection` > `qc_geo_convert_coordinates`

**Réponse (juillet 2026) :**

1. `qc_geo_spatial_intersection(..., layer_type="arrondissements_montreal")` → polygone d'arrondissement (WFS ; si indisponible, réessayer).
2. `qc_geo_convert_coordinates` (WGS84 → EPSG:32198) :

| Entrée (WGS84) | Sortie (Lambert MTQ) |
|----------------|----------------------|
| lon -73.5673, lat 45.5017 | x ≈ -396 122, y ≈ 181 374 |

**Source :** [IGO](https://geoegl.msp.gouv.qc.ca/ws/igo_gouvouvert.fcgi)

---

## Cross-source et scénarios pratiques

### 19. Transport en commun — comparaison multi-portails

**Requête :**
> « Compare ce que Données Québec et donnees.montreal.ca ont comme données sur le transport en commun. »

**Outils utilisés :** `qc_search_datasets` + `mtl_search_datasets`

**Réponse (juillet 2026) :**

| Source | Jeux trouvés | Exemples |
|--------|-------------|---------|
| Données Québec | ~144 | Transport collectif, GTFS |
| donnees.montreal.ca | ~76 | Vision 2050, aménagement TC |

**Sources :** [Données Québec](https://www.donneesquebec.ca/) · [donnees.montreal.ca](https://donnees.montreal.ca/)

---

### 20. Pistes cyclables — recherche multi-sources

**Requête :**
> « Trouve les données sur les pistes cyclables à Montréal via les deux portails et via les couches géospatiales IGO. »

**Outils utilisés :** `qc_search_datasets` + `mtl_search_datasets` + `qc_geo_list_layers`

**Réponse (juillet 2026) :**

| Source | Résultat |
|--------|----------|
| Données Québec / Montréal | Réseau cyclable, REV, GeoJSON/SHP |
| IGO WFS | Pas de couche réseau cyclable municipal |
| IGO WMS | `convi_velo_glv` (convivialité routes MTQ) |

**Jeu clé :** [Réseau cyclable](https://www.donneesquebec.ca/recherche/dataset/vmtl-pistes-cyclables)

**Sources :** [Données Québec](https://www.donneesquebec.ca/) · [donnees.montreal.ca](https://donnees.montreal.ca/) · [IGO](https://geoegl.msp.gouv.qc.ca/ws/igo_gouvouvert.fcgi)

---

### 21. Écoles près de Place Ville-Marie

**Requête :**
> « Quelles écoles / établissements d'enseignement sont près de 1 Place Ville-Marie ? »

**Outils utilisés :** `qc_search_datasets` > `qc_query_resource_data` (jeu provincial) + calcul de distance

**Réponse (juillet 2026) :**

Jeu : [Localisation des établissements d'enseignement](https://www.donneesquebec.ca/recherche/dataset/localisation-des-etablissements-d-enseignement-du-reseau-scolaire-au-quebec)
Filtrer `NOM_MUNCP` ≈ Montréal, colonnes `COORD_Y_LL84` / `COORD_X_LL84`, trier par distance à (45.5017, -73.5673) :

| Établissement | Adresse | Ordre | Distance |
|---|---|---|---|
| Collège des Technologies de l'Information  | 1255, boulevard Robert-Bourassa | Collégial | 219 m |
| Collège des Technologies de l'Information  | 1255, boulevard Robert-Bourassa | Collégial | 219 m |
| École de management INSA | 1255, boulevard Robert-Bourassa | Collégial | 219 m |
| École de management INSA (secteur anglopho | 1255, boulevard Robert-Bourassa | Collégial | 219 m |
| Multihexa | 503, boulevard René-Lévesque Ouest | Collégial | 273 m |
| Multihexa (secteur anglophone) | 503, boulevard René-Lévesque Ouest | Collégial | 273 m |

**Source :** [Données Québec — MEQ/MES](https://www.donneesquebec.ca/recherche/dataset/localisation-des-etablissements-d-enseignement-du-reseau-scolaire-au-quebec)

---

### 22. Stations BIXI près de moi

**Requête :**
> « Quelles stations BIXI sont les plus proches de Place Ville-Marie ? »

**Outils utilisés :** `mtl_bixi_nearby` (préféré) — ou `mtl_search_datasets` + GBFS manuel

**Réponse (juillet 2026) :**

`mtl_bixi_nearby(address="1 Place Ville-Marie, Montreal", radius_m=400, limit=8)` → stations triées par `distance_m` (vélos / bornes libres); chaque station a `google_maps_url`, plus `nearest_google_maps_directions_url` vers la plus proche.

| Station | Capacité | Distance |
|---|---|---|
| Place Ville-Marie (Robert-Bourassa / René-Lévesque) | 33 | ~90 m |
| Union / René-Lévesque | 27 | ~90 m |
| Belmont / Robert-Bourassa | 27 | ~105 m |

**Source :** [BIXI — État des stations](https://donnees.montreal.ca/dataset/bixi-etat-des-stations) · [GBFS](https://gbfs.velobixi.com/gbfs/gbfs.json)

---

### 22b. BIXI près de l'Hôtel de Ville de Montréal

**Requête :**
> « Stations BIXI proches de l'Hôtel de Ville (275 rue Notre-Dame Est) ? »

**Outils utilisés :** `mtl_bixi_nearby`

**Réponse (16 juillet 2026) :**

`mtl_bixi_nearby(address="275 Rue Notre-Dame Est, Montreal", radius_m=400, limit=8)` :

| Dist. | Station | Vélos | Bornes libres |
|---|---|---|---|
| 93 m | du Champ-de-Mars / Gosford | 3 | 20 |
| 146 m | Place des Montréalaises (St-Antoine) | 8 | 9 |
| 199 m | Notre-Dame / St-Gabriel | 0 | 10 |
| 223 m | de la Commune / Place Jacques-Cartier | 49 | 28 |
| 263 m | Métro Champ-de-Mars (Viger / Sanguinet) | 17 | 20 |
| 277 m | Hôtel-de-Ville / Viger | 17 | 5 |

**Source :** [BIXI — État des stations](https://donnees.montreal.ca/dataset/bixi-etat-des-stations)

---

### 23. Grands parcs et espaces publics

**Requête :**
> « Quels parcs sont près de moi au centre-ville ? »

**Outils utilisés :** `mtl_parcs_nearby` (préféré) — ou catalogue + GeoJSON

**Réponse (juillet 2026) :**

`mtl_parcs_nearby(address="1 Place Ville-Marie, Montreal", radius_m=800, parks_only=true)` → parcs / places (`TYPO1` contenant « Parc »), tri `distance_m`.

Astuce : `parks_only=false` pour inclure espaces voirie / autres verts.

**Source :** [Grands parcs Montréal](https://donnees.montreal.ca/dataset/grands-parcs-parcs-d-arrondissements-et-espaces-publics)

---

### 23b. Parcs près de l'Hôtel de Ville de Montréal

**Requête :**
> « Quels parcs / places sont à pied du Hôtel de Ville (275 Notre-Dame Est) ? »

**Outils utilisés :** `mtl_parcs_nearby`

**Réponse (16 juillet 2026) :**

`mtl_parcs_nearby(address="275 Rue Notre-Dame Est, Montreal", radius_m=300, parks_only=false, limit=8)` :

| Dist. | Nom | Type |
|---|---|---|
| 37 m | Champ-de-Mars | Parc de quartier |
| 42 m | Vauquelin | Place publique |
| 46 m | Jardin du Gouverneur | Place publique |
| 46 m | Jardin du Château Ramezay | Espace institutionnel |
| 65 m | Jacques-Cartier | Place publique |
| 118 m | Jacques-Cartier | Place publique |

**Source :** [Espaces verts](https://donnees.montreal.ca/dataset/grands-parcs-parcs-d-arrondissements-et-espaces-publics)

---

## Linguistique, généalogie et Hydro-Québec

### 24. Vitrine linguistique — prépositions et toponymes

**Requête :**
> « Cherche dans la Vitrine linguistique les articles sur les prépositions devant le nom Québec. »

**Outils utilisés :** `qc_oqlf_search` > `qc_oqlf_get_entry`

**Réponse :**

L'agent trouve des fiches BDL / GDT (titres, extraits, URL). Exemple : *Les prépositions devant un nom de province ou de territoire*.

**Source :** [Vitrine linguistique (OQLF)](https://vitrinelinguistique.oqlf.gouv.qc.ca/)

---

### 25. NosOrigines — Samuel de Champlain

**Requête :**
> « Cherche Samuel de Champlain sur NosOrigines. »

**Outils utilisés :** `qc_nosorigines_search`

**Réponse :**

Résultats en **tableau** (nom, dates, liens pid). Personnages historiques publics seulement ; les affichages « Privé » restent protégés.

**Source :** [NosOrigines](https://www.nosorigines.qc.ca/genealogieSearch.aspx?lng=fr)

Ensuite : fiche détaillée → §48 (`qc_nosorigines_get_person`) ; parents / grands-parents → §49 (`qc_nosorigines_get_ancestors`).

---

### 26. Hydro-Québec — état du service (Info-pannes)

**Requête :**
> « Y a-t-il une panne d'électricité à 1 Place Ville-Marie, Montréal ? »

**Outils utilisés :** `qc_hydro_outage_status`

**Réponse (exemple) :**

`qc_hydro_outage_status(address="1 Place Ville-Marie, Montréal")` résout l'adresse civique puis interroge Info-pannes :

| Champ | Exemple |
|-------|---------|
| `etat` / `etat_label` | A / Alimentation normale (selon le moment) |
| `lieuConsommation` | Identifiant Hydro |
| `interruptions` | Liste vide si aucun incident |

Données approximatives (wrapper communautaire). Préférer une adresse complète (numéro + rue) ; lat/lng via reverse ICherche si besoin.

**Source :** [Info-pannes Hydro-Québec](https://infopannes.solutions.hydroquebec.com)

---

## Montréal catalogue (`mtl_*`)

### 27. Top 10 des postes de quartier — actes criminels

**Requête :**
> « Quels sont les 10 postes de quartier avec le plus d'actes criminels à Montréal ? »

**Outils utilisés :** `mtl_search_datasets` > `mtl_query_sql`

**Réponse (juillet 2026) :**

Le dataset SPVM utilise `PDQ` (pas d'arrondissement). `mtl_query_sql` enrichit avec `pdq_label` / `pdq_name`.

| Rang | PDQ | Total actes |
|------|-----|-------------|
| 1 | 38 (Plateau-Mont-Royal) | 25 787 |
| 2 | 21 (Centre-Sud / Ville-Marie Est) | 23 934 |
| 3 | 20 (Ville-Marie Ouest) | 20 700 |
| 4 | 48 (Mercier-Hochelaga-Maisonneuve) | 16 615 |
| 5 | 26 (Côte-des-Neiges / Outremont) | 16 573 |

Totaux sur toute la période du jeu (pas les stats mensuelles officielles SPVM).

**Sources :** [Actes criminels](https://donnees.montreal.ca/dataset/actes-criminels) · [limites-pdq-spvm](https://donnees.montreal.ca/dataset/limites-pdq-spvm)

---

### 28. Introductions par effraction vs vols de véhicules

**Requête :**
> « Compare le nombre d'introductions par effraction vs les vols de véhicules par PDQ. »

**Outils utilisés :** `mtl_query_sql` (1 requête SQL avec `CASE`)

**Réponse (juillet 2026) :**

| PDQ | Introductions | Vols véhicules |
|-----|---------------|----------------|
| 38 (Plateau-Mont-Royal) | 8 427 | 4 210 |
| 26 (Côte-des-Neiges / Outremont) | 4 292 | 3 598 |
| 23 (Hochelaga-Maisonneuve) | 4 288 | 1 822 |
| 15 (Sud-Ouest) | 4 175 | 2 190 |
| 21 (Centre-Sud / Ville-Marie Est) | 3 960 | 2 592 |
| 48 (Mercier-Hochelaga-Maisonneuve) | 3 789 | 3 924 |
| 44 (Rosemont) | 3 755 | 2 664 |
| 35 (Petite-Patrie) | 3 486 | 1 617 |
| 39 (Montréal-Nord) | 3 327 | 4 182 |

**Observation :** Le PDQ 39 (Montréal-Nord) et le PDQ 48 se distinguent par un ratio élevé de vols de véhicules.

**Source :** [Actes criminels](https://donnees.montreal.ca/dataset/actes-criminels)

---

### 29. Tendance mensuelle des actes criminels

**Requête :**
> « Montre la tendance mensuelle des actes criminels à Montréal. »

**Outils utilisés :** `mtl_query_sql`

**Réponse :** tableau mois × total (agrégation SQL sur la colonne `DATE`).

**Source :** [Actes criminels](https://donnees.montreal.ca/dataset/actes-criminels)

---

### 30. Qualité de l'eau à Montréal (QUALO)

**Requête :**
> « Quelle est la qualité de l'eau de rive près du Vieux-Port / Hôtel de Ville (275 Notre-Dame Est) ? »

**Outils utilisés :** `mtl_qualo_nearby` (préféré) — ou `mtl_neighborhood_briefing` pour un briefing complet

**Réponse (16 juillet 2026) :**

`mtl_qualo_nearby(address="275 Rue Notre-Dame Est, Montreal", radius_m=1500, limit=5)` :

| Dist. | Station | Plan d'eau | Date | Temp. | pH | Colif. fécaux |
|---|---|---|---|---|---|---|
| 530 m | Plage de l'Horloge (FSL-205) | Fleuve Saint-Laurent | 2026-07-07 | 24 °C | 8.1 | 8 |
| 575 m | Marina du Vieux-Port (FSL-200) | Fleuve Saint-Laurent | 2026-07-07 | 24 °C | 8.0 | 2 |
| 1,4 km | Parc Cité-du-Havre (BLAP-8.5) | Bassin de Laprairie | 2026-07-07 | 23 °C | 8.3 | 3 |

Seuil baignade usuel ~200 UFC/100 mL — ces points sont largement en dessous. Voir aussi **Â§22b** / **Â§23b** / **Â§45**.

**Source :** [QUALO — RSMA](https://donnees.montreal.ca/dataset/rsma-qualite-de-l-eau-en-rive-qualo)

---

### 31. Arbres publics par arrondissement

**Requête :**
> « Combien d'arbres publics par arrondissement à Montréal ? »

**Outils utilisés :** `mtl_search_datasets` > `mtl_query_data` > `mtl_query_sql`

**Réponse :** classement en **tableau** arrondissement × nombre (re-interroger pour totaux à jour).

**Source :** [donnees.montreal.ca](https://donnees.montreal.ca/)

---

## La bicyclette (`mtl_labicyclette_*`)

### 32. Vue d'ensemble des compteurs

**Requête :**
> « Donne-moi la vue d'ensemble La bicyclette (volume, compteurs actifs). »

**Outils utilisés :** `mtl_labicyclette_overview`

**Réponse (juillet 2026) :**

| Indicateur | Valeur |
|---|---|
| Total Rides | 180.3M |
| Active Counters | 81 |
| Daily Average | 28.2K |

Ignorer tout objet `chart` en chat ; présenter les KPI en tableau.

**Source :** [labicyclette.ca](https://labicyclette.ca/)

---

### 33. Compteur Berri — série compacte

**Requête :**
> « Liste les compteurs à Ville-Marie, puis le détail du compteur Berri. »

**Outils utilisés :** `mtl_labicyclette_list_counters` > `mtl_labicyclette_get_counter`

**Réponse :**

1. `mtl_labicyclette_list_counters(arrondissement="Ville-Marie", limit=20)` → trouver l'`instance`.
2. `mtl_labicyclette_get_counter(..., include_weather=false)` → résumé + série journalière en **tableau** date/volume.

**Source :** [labicyclette.ca](https://labicyclette.ca/)

---

### 34. Boroughs et chantiers

**Requête :**
> « Volumes par arrondissement et chantiers bloquant le réseau. »

**Outils utilisés :** `mtl_labicyclette_boroughs` + `mtl_labicyclette_list_construction`

**Réponse (juillet 2026) :**

`mtl_labicyclette_boroughs()` (totaux all-time) :

| Rang | Arrondissement | Volume | Part | Compteurs |
|------|----------------|--------|------|-----------|
| 1 | Le Plateau-Mont-Royal | 64.2M | 35.7 % | 11 |
| 2 | Ville-Marie | 56.5M | 31.4 % | 20 |
| 3 | Rosemont–La Petite-Patrie | 28.8M | 16.0 % | 9 |
| 4 | Ahuntsic-Cartierville | 7.5M | — | 9 |

`mtl_labicyclette_list_construction(status="blocked", limit=10)` → sites slim (ignorer `chart` en chat).

**Source :** [labicyclette.ca](https://labicyclette.ca/)

---

## Collecte MTL (`mtl_collecte_*`)

### 35. Calendrier de collecte par adresse

**Requête :**
> « Quel est le calendrier de collecte au 275 Rue Notre-Dame Est ? »

**Outils utilisés :** `mtl_collecte_find_waste`

**Réponse (juillet 2026) :**

Adresse résolue : **Hôtel de Ville / 275 Rue Notre-Dame Est** (≈ 45.509, -73.554), secteur **VM-2**.

| Flux | Jour(s) typique(s) | Secteur |
|------|-------------------|---------|
| Ordures ménagères | lundi | VM-2 |
| Recyclage / organiques | voir `collections` live | VM-* |

Fenêtre de dépôt : entre 19 h la veille et 7 h le jour de la collecte.

**Source :** [Collecte MTL](https://www.collectemtl.ca/)

---

### 36. Écocentres et stats d'arrondissement

**Requête :**
> « Écocentres près du Vieux-Montréal, et bilan massique de l'arrondissement. »

**Outils utilisés :** `mtl_collecte_find_ecocentres` > `mtl_collecte_borough_waste_stats`

**Réponse (juillet 2026) :**

Écocentres les plus proches de (45.509, -73.554) :

| Écocentre | Arrondissement | Adresse |
|-----------|----------------|---------|
| La Petite-Patrie | Rosemont–La Petite-Patrie | 1100, rue des Carrières |

Puis `mtl_collecte_borough_waste_stats(...)` pour le bilan massique de l'arrondissement.

**Source :** [Collecte MTL](https://www.collectemtl.ca/)

---

## Murales (`mtl_murales_*`)

### 37. Recherche et détail

**Requête :**
> « Murales du Plateau depuis 2020, puis détail de la murale 307. »

**Outils utilisés :** `mtl_murales_search` > `mtl_murales_get`

**Réponse (juillet 2026) :**

`mtl_murales_search(arrondissement="Plateau", annee_min="2020", page_size=5)` → **12** résultats (échantillon) :

| Id | Artiste | Adresse | Année | Arrondissement |
|---|---|---|---|---|
| 241 | Octavio Ruest | 1380 Gilford | 2021 | Le Plateau-Mont-Royal |
| 247 | Vincent Tourigny | 4231 avenue Des Érables | 2021 | Le Plateau-Mont-Royal |
| 263 | Teddy Kelly | 5730 boulevard Saint-Laurent | 2021 | Le Plateau-Mont-Royal |
| 280 | Marc Séguin | 625, rue Milton (angle University) | 2022 | Le Plateau-Mont-Royal |
| 283 | Projet TYXNA | 3725 boulevard Saint-Laurent | 2023 | Le Plateau-Mont-Royal |

`mtl_murales_get(murale_id="307")` → fiche détaillée + image.

**Sources :** [donnees.montreal.ca/murales](https://donnees.montreal.ca/dataset/murales) · [mtlmurales.ca](https://www.mtlmurales.ca/fr)

---

### 38. À proximité, au hasard, facettes

**Requête :**
> « Murales près du centre-ville, une au hasard à Ville-Marie, et le décompte par arrondissement. »

**Outils utilisés :** `mtl_murales_nearby` > `mtl_murales_random` > `mtl_murales_facet`

**Réponse :**

1. `mtl_murales_nearby(latitude=45.5088, longitude=-73.5617, radius_m=800)` → tri `distance_m`; pin `google_maps_url` par murale + `nearest_google_maps_directions_url`.
2. `mtl_murales_random(arrondissement="Ville-Marie", count=1)`.
3. `mtl_murales_facet(facet="arrondissement")` → tableau compteurs.

**Sources :** [donnees.montreal.ca/murales](https://donnees.montreal.ca/dataset/murales) · [mtlmurales.ca](https://www.mtlmurales.ca/fr)

---

## Avis et alertes (`mtl_avis_*`)

### 39. Avis près d'une adresse / d'un point

**Requête :**
> « Quels avis/alertes sont actifs près de Place Ville-Marie le 16 juillet 2026 ? »

**Outils utilisés :** `mtl_avis_nearby`

**Réponse (juillet 2026) :**

`mtl_avis_nearby(date="2026-07-16", address="1 Place Ville-Marie, Montreal", radius_m=800, limit=5)` → avis triés par `distance_m`. Le géocodeur iCherche demande `geometry=true` (géré par le serveur).

**Sources :** [avis-alertes](https://donnees.montreal.ca/dataset/avis-alertes) · [montreal.ca/avis-et-alertes](https://montreal.ca/avis-et-alertes)

---

## Autour d'une adresse (Vieux-Montréal)

### 39b. Chaîne unitaire (équivalent manuel du briefing)

**Requête :**
> « Événements / avis publics près de l'Hôtel de Ville ; Hydro-Québec ; qualité de l'eau ; parcs ; BIXI proches. »

**Outils utilisés :** `mtl_avis_nearby` > `qc_hydro_outage_status` > `mtl_qualo_nearby` > `mtl_parcs_nearby` > `mtl_bixi_nearby`

**Réponse :** préférer **Â§45** `mtl_neighborhood_briefing` (un seul appel). Chaîne manuelle si une seule section est requise :

1. `mtl_avis_nearby(date="2026-07-16", address="275 Rue Notre-Dame Est, Montreal", radius_m=1000)`
2. `qc_hydro_outage_status(address="275 Rue Notre-Dame Est, Montreal")`
3. `mtl_qualo_nearby(address=…, radius_m=1500)`
4. `mtl_parcs_nearby(address=…, radius_m=300, parks_only=false)`
5. `mtl_bixi_nearby(address=…, radius_m=400)`

Présenter chaque bloc en **tableau markdown** (Dist. en 1re colonne) ; source sous chaque section. Détails unitaires : **Â§30** (QUALO), **Â§22b** (BIXI), **Â§23b** (parcs). Modèle stylé composite : **Â§45**.

**Sources :** [avis-alertes](https://donnees.montreal.ca/dataset/avis-alertes) · [Info-pannes](https://infopannes.solutions.hydroquebec.com) · [QUALO](https://donnees.montreal.ca/dataset/rsma-qualite-de-l-eau-en-rive-qualo) · [parcs](https://donnees.montreal.ca/dataset/grands-parcs-parcs-d-arrondissements-et-espaces-publics) · [BIXI](https://donnees.montreal.ca/dataset/bixi-etat-des-stations)

---

## Festivals (`mtl_piknic_*` / `mtl_jazzfest_*`)

### 40. OfF Piknic — liste

**Requête :**
> « Liste la programmation OfF Piknic. »

**Outils utilisés :** `mtl_piknic_search_off`

**Réponse :**

`mtl_piknic_search_off(query="", limit=10)` → événements `category: off` en **tableau** (scène, artistes, horaires). Si le HTML est incomplet : `events: []` + `warning`.

**Source :** [Piknic Électronik](https://piknicelektronik.com/)

---

### 41. Piknic — recherche artiste

**Requête :**
> « Cherche Mandragora dans la programmation Piknic. »

**Outils utilisés :** `mtl_piknic_search`

**Réponse :** tableau date / scène / artistes (série principale, pas OfF / Petit).

**Source :** [Piknic Électronik](https://piknicelektronik.com/)

---

### 42. Petit Piknic — dimanche

**Requête :**
> « Programme Petit Piknic du 19 juillet 2026. »

**Outils utilisés :** `mtl_piknic_search_petit`

**Réponse :** `mtl_piknic_search_petit(date="2026-07-19")` → tableau.

**Source :** [Piknic Électronik](https://piknicelektronik.com/)

---

### 43. Jazz Fest — concerts gratuits

**Requête :**
> « Liste des concerts gratuits du Festival de Jazz. »

**Outils utilisés :** `mtl_jazzfest_search_free`

**Réponse :**

`mtl_jazzfest_search_free(query="", limit=25)` → concerts `category: free`. Si la page est JS-only : `events: []` + `warning` (pas une erreur outil).

**Source :** [FIJM — Horaire](https://montrealjazzfest.com/fr/programmation/horaire)

---

### 44. Jazz Fest — concerts payants

**Requête :**
> « Cherche Isaiah Collier dans la programmation payante du Jazz Fest. »

**Outils utilisés :** `mtl_jazzfest_search_paid`

**Réponse :** spectacles payants en tableau, ou liste vide + `warning` si le HTML statique n'expose pas l'horaire. Les lignes datées incluent `google_calendar_url` ; coller `calendar_ascii` si présent.

**Source :** [FIJM — Horaire](https://montrealjazzfest.com/fr/programmation/horaire)

---

### 44b. Événements publics (calendrier civique)

**Requête :**
> « Quels événements publics à Montréal le 19 juillet 2026 ? »

**Outils utilisés :** `mtl_evenements_search`

**Réponse :**

`mtl_evenements_search(query="", date="2026-07-19", limit=10)` → lignes avec `google_calendar_url` ; coller `calendar_ascii` (agenda jour). Source CKAN primaire : Données Québec (`vmtl-evenements-publics`).

**Source :** [Données Québec — vmtl-evenements-publics](https://www.donneesquebec.ca/recherche/?q=vmtl-evenements-publics)

---

### 44c. Agenda de la semaine

**Requête :**
> « Qu'est-ce qu'il y a cette semaine à Montréal (festivals, culture, avis près du centre-ville) ? »

**Outils utilisés :** `mtl_calendar_week`

**Réponse :**

`mtl_calendar_week(week_start="2026-07-13", address="800 Rue De La Gauchetiere Ouest, Montreal")` → `items[]` unifiés + `calendar_ascii` + liens Google Calendar. Sans adresse/coords, les avis sont omis (`warning`).

**Sources :** Piknic / Jazz Fest / [événements publics](https://www.donneesquebec.ca/) / [avis-alertes](https://donnees.montreal.ca/dataset/avis-alertes)

---

## Briefing de quartier (`mtl_neighborhood_briefing`)

### 45. Briefing multi-domaines — Hôtel de Ville de Montréal

**Requête :**
> « Briefing de quartier à l'Hôtel de Ville (275 rue Notre-Dame Est), Montréal, pour le 16 juillet 2026 : Hydro, avis/alertes ≤ 1 km, qualité de l’eau de rive (QUALO), parcs à pied (~300 m), stations BIXI (~400 m). »

**Outils utilisés :** `mtl_neighborhood_briefing`

**Réponse (16 juillet 2026 — instantané) :**

Autour de l'**Hôtel de Ville de Montréal** (275 rue Notre-Dame Est, ≈ 45.509, −73.554) : plusieurs avis ≤ 1 km, eau de rive bonne aux stations proches, plusieurs parcs et BIXI à pied. (Hydro Info-pannes peut être indisponible ponctuellement.)

#### Avis / alertes publics (≤ 1 km)

| Dist. | Type | Titre |
|---|---|---|
| 12 m | Urgence | Avertissement de chaleur en vigueur |
| 271 m | Circulation | Fermeture Av. de l'Hôtel-de-Ville (Viger ↔ René-Lévesque) |
| 614 m | Circulation | Entrave Rue de la Commune Ouest |
| 745 m | Circulation | Fermeture Rue Wolfe |
| 779 m | Circulation | Entrave Rue Atateken (sud) |

**Source :** [Avis et alertes](https://montreal.ca/avis-et-alertes) · [dataset](https://donnees.montreal.ca/dataset/avis-alertes)

#### Hydro-Québec (Info-pannes)

Vérifier en live via `qc_hydro_outage_status` / le portail Info-pannes (l'API peut renvoyer HTTP 400 selon le moment).

**Source :** [Info-pannes](https://infopannes.solutions.hydroquebec.com)

#### Qualité de l’eau (QUALO)

| Dist. | Plan d’eau | Temp. | Colif. fécaux |
|---|---|---|---|
| 424 m | Fleuve Saint-Laurent | 24 °C | 2 |
| 762 m | Fleuve Saint-Laurent | 24 °C | 8 |
| 1,3 km | Bassin de Laprairie | 23 °C | 3 |

Seuil baignade usuel ~200 UFC/100 mL — ces points sont largement en dessous.

**Source :** [QUALO](https://donnees.montreal.ca/dataset/rsma-qualite-de-l-eau-en-rive-qualo)

#### Parcs proches (≤ ~300 m)

| Dist. | Parc / place | Type |
|---|---|---|
| 37 m | Champ-de-Mars | Parc de quartier |
| 42 m | Vauquelin | Place publique |
| 46 m | Jardin du Gouverneur | Place publique |
| 65 m | Jacques-Cartier | Place publique |

**Source :** [Espaces verts](https://donnees.montreal.ca/dataset/grands-parcs-parcs-d-arrondissements-et-espaces-publics)

#### BIXI (≤ 400 m, GBFS)

| Dist. | Station | Vélos | Bornes libres |
|---|---|---|---|
| 93 m | du Champ-de-Mars / Gosford | 3 | 20 |
| 146 m | Place des Montréalaises (St-Antoine) | 8 | 9 |
| 223 m | de la Commune / Place Jacques-Cartier | 49 | 28 |
| 277 m | Hôtel-de-Ville / Viger | 17 | 5 |

**Source :** [État des stations BIXI](https://donnees.montreal.ca/dataset/bixi-etat-des-stations)

Appel type :

```text
mtl_neighborhood_briefing(
  address="275 Rue Notre-Dame Est, Montreal",
  date="2026-07-16",
  avis_radius_m=1000,
  parks_radius_m=300,
  bixi_radius_m=400,
  qualo_radius_m=1500,
  limit=10,
)
```

Les totaux live évoluent ; une section en erreur (`error`) n’annule pas le reste du briefing.

---

## Contexte utilisateur + événements bientôt

### 46. Contexte GPS / date (`common_get_context`)

**Requête :**
> « Quelle est ma date locale et ma position approximative pour chercher près de moi ? »

**Outils utilisés :** `common_get_context`

Passez le GPS téléphone/PC et le fuseau système quand disponibles :

```text
common_get_context(
  latitude=45.5088,
  longitude=-73.5617,
  timezone="America/Toronto",
)
```

Sans GPS : l’outil peut utiliser l’IP **client** (`X-Forwarded-For`) — jamais l’IP du serveur MCP (Vercel/Docker). Réponse : `now.date`, `now.datetime_iso`, `location.location_source` (`agent` | `address` | `client_ip`).

**Source :** contexte MCP (fuseau `America/Toronto` par défaut)

### 47. Qu’est-ce qu’il y a bientôt ? (`mtl_events_soon`)

**Requête :**
> « Qu’est-ce qu’il y a comme spectacles / événements publics dans les prochaines 24 h près de moi ? »

**Outils utilisés :** `mtl_events_soon` (idéalement après `common_get_context`)

```text
mtl_events_soon(
  hours=24,
  latitude=45.5088,
  longitude=-73.5617,
  limit=15,
)
```

Retourne `items[]` + `calendar_ascii` + `google_calendar_url`. Les festivals n’ont pas de coords GPS ; le filtre lieu approx ne s’applique qu’aux événements civiques.

**Sources :** [Piknic](https://piknicelectronik.com/fr/programmation) / [Jazz Fest](https://montrealjazzfest.com/fr/programmation/horaire) / [événements publics](https://www.donneesquebec.ca/recherche/?q=vmtl-evenements-publics)

---

## NosOrigines — fiche et ancêtres

### 48. NosOrigines — fiche François Boucher (`qc_nosorigines_get_person`)

**Requête :**
> « Ouvre la fiche NosOrigines de François Boucher (pid 781) : parents, conjoint, mariage, enfants. »

**Outils utilisés :** `qc_nosorigines_get_person`

```text
qc_nosorigines_get_person(pid="781")
```

**Réponse (tableau) :**

| Champ | Valeur |
| --- | --- |
| Nom | Francois Boucher |
| Baptême | 22 novembre 1617 — St-Langis-les-Mortagne, Perche, France |
| Père | Marin Boucher (pid 774) |
| Mère | Julienne Baril (pid 780) |
| Conjoint(e) | Florence Gareman (pid 782) |
| Mariage | 03 septembre 1641 — Notre-Dame, Québec |

Les fiches de personnes vivantes peuvent afficher **Privé** / `****` : ne pas inventer le nom (ne pas utiliser les meta HTML).

**Source :** [François Boucher — NosOrigines](https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?genealogie=Boucher_Francois&pid=781)

---

### 49. NosOrigines — ancêtres / grand-père paternel (`qc_nosorigines_get_ancestors`)

**Requête :**
> « Remonte les parents de François Boucher (pid 781) ; qui est le père (côté paternel) ? »

**Outils utilisés :** `qc_nosorigines_get_ancestors`

```text
qc_nosorigines_get_ancestors(pid="781", generations=1)
```

| Lien | Personne |
| --- | --- |
| Personne | Francois Boucher (781) |
| Père (`father.person`) | Marin Boucher (774) |
| Mère (`mother.person`) | Julienne Baril (780) |

Pour les **grands-parents**, utilisez `generations=2` (ou un second appel sur le pid du père). Le grand-père paternel est `father.father` (ou `father.person` puis ses parents). Les beaux-parents (`spouse_father` / `spouse_mother` sur la fiche) ne sont pas remontés par cet outil.

**Source :** [NosOrigines](https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?pid=781)

---

[Retour au README](README.md)
