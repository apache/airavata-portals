# {{ cookiecutter.project_name }}

## Getting Started

1. Follow the instructions for installing the
   [Airavata Django Portal](https://github.com/apache/airavata-django-portal)
2. With the Airavata Django Portal virtual environment activated, clone this
   repo and install it into the portal's virtual environment

   ```
   cd {{ cookiecutter.project_slug }}
   pip install -e .
   ```

3. If this app serves its own pages, build the Vite frontend so the portal can
   load its bundle:

   ```
   cd {{ cookiecutter.project_slug }}/static/{{ cookiecutter.project_slug }}
   npm install
   npm run build     # or `npm run watch` while developing
   ```

4. Start (or restart) the Django Portal server.
