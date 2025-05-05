from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    KC_RS256_PUBLIC_KEY: str

    LOGS_FILE: str = 'logs.log'

    @property
    def kc_public_key(self) -> str:
        key_begin = '-----BEGIN PUBLIC KEY-----\n'
        key_end = '\n-----END PUBLIC KEY-----'
        key = self.KC_RS256_PUBLIC_KEY
        if not key.startswith(key_begin):
            key = f'{key_begin}{key}'
        if not key.endswith(key_end):
            key = f'{key}{key_end}'
        return key

    model_config = SettingsConfigDict(
        env_file='config/.env',
        extra='ignore',
    )


settings = Settings()
