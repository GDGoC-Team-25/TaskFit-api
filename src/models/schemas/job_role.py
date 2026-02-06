from pydantic import BaseModel


class JobRoleResponse(BaseModel):
    id: int
    category: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class JobRoleBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
