import i18n
from app import App
from settings import SettingsManager

if __name__ == "__main__":
    SettingsManager.apply_to_config()
    app = App()
    app.mainloop()
