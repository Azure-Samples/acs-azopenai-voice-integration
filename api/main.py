from src.core.app import CallAutomationApp

# Create application instance
app_instance = CallAutomationApp()
# Get the Quart app instance
app = app_instance.app

if __name__ == "__main__":
    app_instance.run()
