from pydantic import BaseModel


class CompanyResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    logo_url: str | None = None

    model_config = {"from_attributes": True}


class CompanyBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
