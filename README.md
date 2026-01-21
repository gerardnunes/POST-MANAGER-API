# Post manager API 🚀

Descrição do Projeto:
Este projeto é uma plataforma de social media completa, desenvolvida com foco em escalabilidade, segurança e facilidade de uso. Ele combina um backend robusto em Python com Flask e SQLAlchemy com um frontend responsivo.

🛠️
### **Backend**
- Autenticação e autorização de usuários (Admin, Social Media, Cliente) com segurança via `Werkzeug`.
- Controle de permissões baseado em papéis e status de usuário.
- CRUD completo para:
  - **Usuários** (clientes, social media, admin)
  - **Projetos**
  - **Posts**
  - **Mídias** (uploads de arquivos com controle de tamanho e tipo)
  - **Feedbacks** (respostas e acompanhamento de revisões)
- Upload e download seguro de arquivos, com prevenção de path traversal.
- Logs e flashes para rastrear erros e informar ações realizadas.
- Painéis personalizados para cada tipo de usuário:
  - Cliente: acompanhar status de projetos e posts, enviar feedbacks.
  - Social Media: gerenciar projetos, criar posts, responder feedbacks.
  - Admin: visão geral do sistema, estatísticas e gerenciamento de usuários e projetos.

### **Frontend**
- Interfaces responsivas usando HTML, CSS e templates Jinja2.
- Dashboards intuitivos para cada papel de usuário.
- Formulários para criação e edição de projetos, posts e feedbacks.
- Upload de arquivos com preview e suporte a múltiplos formatos.
- Mensagens de feedback (flashes) para indicar sucesso ou erro das operações.

## 🛠️ Tecnologias e Ferramentas
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)  
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)  
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-FF0000?style=flat&logo=sqlalchemy&logoColor=white)  
![Werkzeug](https://img.shields.io/badge/Werkzeug-000000?style=flat)  
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)  
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)  
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)  
