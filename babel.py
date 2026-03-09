from fastapi_babel import Babel, BabelConfigs, BabelMiddleware

configs = BabelConfigs(
    ROOT_DIR=__file__,
    BABEL_DEFAULT_LOCALE="en",
    BABEL_TRANSLATION_DIRECTORY="lang",
)
app.add_middleware(BabelMiddleware, babel_configs=configs)

if __name__ == "__main__":
    Babel(configs).run_cli()
