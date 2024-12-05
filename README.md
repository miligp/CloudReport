# Nom du Projet : Application Galerie de Photos

## Description
Ce projet est une application web permettant aux utilisateurs de :
- Télécharger des photos sur un stockage Azure Blob.
- Afficher une galerie d'images sous forme de grille.
- Associer un identifiant utilisateur à chaque photo.
- Gérer les utilisateurs (inscription, connexion, déconnexion).

L'application utilise **Flask** comme framework backend et s'intègre à plusieurs services Azure, dont SQL Database et Blob Storage.

---

## Fonctionnalités
- **Gestion des utilisateurs** : inscription, connexion et déconnexion sécurisées.
- **Téléversement de photos** : stockage des images dans un conteneur Azure Blob.
- **Affichage de galerie** : affichage des photos uploadées avec l'identifiant de l'utilisateur.
- **Suppression des photos** : chaque utilisateur peut supprimer ses propres photos.

---

## Architecture

### Schéma

project/

├── app.py

├── templates/

│   ├── index.html

│   ├── upload.html

│   ├── register.html

│   ├── error.html

│   ├── base.html

│   ├── login.html

│   ├── user.html

├── static/

│   ├── css/

│   │   ├── styles.css

├── README.md

├── requirements.txt


### Services Azure utilisés :
1. **Azure Blob Storage** 
2. **Azure SQL Database** 
3. **Azure WebApp** 

---

## Installation et Exécution
### Prérequis
- Python 3.10 ou supérieur
- Un compte Azure pour les services SQL et Blob Storage
- Une connexion internet stable

### Étapes d'installation
1. Clonez le dépôt :
   ```bash
   git clone https://github.com/miligp/CloudReport.git
   cd CloudApp

   ## Défis Rencontrés

- **Configurer Azure SQL** : Gestion sécurisée des données des utilisateurs et des photos.
- **Problèmes de connexion** : Résolution des erreurs de connexion liées aux paramètres incorrects de la base de données.
- **Compatibilité des environnements** : Adaptation entre l'environnement de développement local et le déploiement sur Azure.
- **Gestion des secrets** : Utilisation des secrets GitHub Actions pour sécuriser les informations sensibles.

---

## Améliorations Futures

- **Ajout de fonctionnalités de tags et de filtres** : Permettre une navigation plus intuitive et personnalisée des photos.
- **Profils utilisateurs** : Implémenter des pages de profil pour chaque utilisateur pour une expérience plus personnalisée.
- **Gestion des erreurs** : Améliorer la gestion des erreurs pour rendre l'expérience utilisateur plus fluide.
- **Azure Cognitive Services** : Intégrer des outils d'analyse pour l'étiquetage automatique et l'amélioration des métadonnées des photos.

---

## Contributeurs

- **Milena Gordien Piquet** 

---

## Licence

Ce projet est sous licence **MIT**. Consultez le fichier [LICENSE](./LICENSE) pour plus de détails.
