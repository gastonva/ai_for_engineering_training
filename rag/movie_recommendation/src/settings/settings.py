from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    VectorDBConnection: str | None = None
    DBConnection: str | None = None
    CollectionName: str | None = None
    API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    AccessTokenExpiresMinutes: int | None = None
    JWTSigningKey: str | None = None
    AcceptCookie: bool = True
    AcceptToken: bool = True
    LangfuseSecretKey: str | None = None
    LangfusePublicKey: str | None = None
    LangfuseHost: str | None = None
    SERPER_API_KEY: str | None = None
    SerperURL: str | None = None
    SearchSources: list[str] | None = None


settings = ProjectSettings()
