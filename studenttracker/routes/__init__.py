from .api import bp as api_bp
from .auth import bp as auth_bp
from .dashboards import bp as main_bp

print("🔄 Attempting to import classes blueprint...")
try:
    from .classes import bp as classes_bp
    print("✅ Classes blueprint imported successfully")
except Exception as e:
    print(f"❌ Failed to import classes blueprint: {e}")
    import traceback
    print(traceback.format_exc())
    classes_bp = None


def register_blueprints(app):
    print("📋 Registering blueprints...")
    app.register_blueprint(main_bp, url_prefix="/app")
    print("✅ Main blueprint registered")
    app.register_blueprint(auth_bp, url_prefix="/app")
    print("✅ Auth blueprint registered")
    app.register_blueprint(api_bp, url_prefix="/app")
    print("✅ API blueprint registered")
    
    if classes_bp:
        try:
            app.register_blueprint(classes_bp, url_prefix="/app/classes")
            print("✅ Classes blueprint registered successfully")
            
            # Debug: Print all routes after registration
            print("🔍 All registered routes:")
            for rule in app.url_map.iter_rules():
                if 'classes' in rule.rule:
                    print(f"   {rule.rule} -> {rule.endpoint}")
                    
        except Exception as e:
            print(f"❌ Failed to register classes blueprint: {e}")
            import traceback
            print(traceback.format_exc())
    else:
        print("❌ Classes blueprint is None, skipping registration")
