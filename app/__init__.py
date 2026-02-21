def create_app():
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True, template_folder='../templates')
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from . import models
        from . import routes
        app.register_blueprint(routes.main)

    return app