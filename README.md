# Exemple— Extraction des appels d'offres

## Description

`MoussaConsulting
Extraction BOAMP` est une application permettant d'extraire et de consulter des **appels d'offres** depuis un site web"boamp", en fonction du **secteur sélectionné** et de la **date d'extraction**.

L'application permet à l'utilisateur de sélectionner un secteur et une date afin d'extraire uniquement les appels d'offres correspondant aux critères demandés.

## Authentification

Pour accéder à l'application, utiliser les identifiants suivants :

```
Nom d'utilisateur : admin
Mot de passe       : changeme
```

> Ces identifiants sont fournis uniquement à titre d'exemple pour l'environnement de démonstration.

## Fonctionnement

Le principe d'extraction est simple :

1. L'utilisateur se connecte à l'application.
2. Il sélectionne le **secteur** souhaité.
3. Il indique la **date d'extraction**.
4. Le système recherche les appels d'offres correspondant au secteur et à la date sélectionnés.
5. Les résultats extraits sont affichés à l'utilisateur.

### Exemple

Si l'utilisateur sélectionne :

```text
Secteur : Informatique
Date d'extraction : 13/08/2026
```

Le système va extraire les appels d'offres correspondant au secteur **Informatique** selon la date d'extraction indiquée.

## Filtres d'extraction

Les principaux critères utilisés sont :

* **Secteur**
* **Date d'extraction**

Ces critères permettent de limiter les résultats et d'obtenir uniquement les appels d'offres correspondant aux besoins de l'utilisateur.

## Exemple de résultat

Après l'extraction, les appels d'offres peuvent contenir différentes informations, par exemple :

```text
Titre de l'appel d'offres
Secteur
Date de publication
Date limite
Organisme
Description
Lien vers l'appel d'offres
```

## Objectif

L'objectif de `readme.tn` est de faciliter la **collecte automatique des appels d'offres** et leur consultation selon différents secteurs et dates, afin d'éviter une recherche manuelle sur le site source.
