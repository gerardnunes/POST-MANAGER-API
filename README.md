# Social Media API 🚀

Descrição do Projeto:
Este projeto é uma plataforma de social media completa, desenvolvida com foco em escalabilidade, segurança e facilidade de uso. Ele combina um backend robusto em Python com Flask e SQLAlchemy com um frontend responsivo.

🛠️ Backend

Framework: Flask

Banco de Dados: SQLAlchemy + SQLite/PostgreSQL

Autenticação & Autorização: Flask-Login + hashing seguro de senhas com Werkzeug

APIs RESTful: endpoints para usuários, posts, comentários, curtidas e seguidores

Validação de Dados: formulários, requisições JSON e tratamento de exceções para evitar falhas

Upload de Arquivos: suporte para envio de imagens e vídeos nos posts, com armazenamento seguro

Segurança: proteção contra SQL Injection, validação de inputs e controle de permissões por usuário


Exemplo de endpoints:

POST /login – autenticação de usuário

POST /register – cadastro de novo usuário

GET /posts – listar todos os posts

POST /posts – criar um novo post
